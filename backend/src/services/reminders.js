import db from '../database.js';

import { sendEmail } from './email.js';



const REMINDER_DAYS = [10, 7, 3, 1, 0];



function formatRwf(amount) {

  return `${new Intl.NumberFormat('en-RW').format(Number(amount) || 0)} Frw`;

}



function formatDate(date) {

  return new Date(date + 'T00:00:00').toLocaleDateString('en-GB', {

    year: 'numeric', month: 'long', day: 'numeric',

  });

}



function getReminderKey(daysLeft) {

  if (daysLeft < 0) return 'overdue';

  if (daysLeft === 0) return 'due_today';

  return `days_${daysLeft}`;

}



function getPaymentLabel(paymentType) {

  return paymentType === 'hygiene'

    ? { en: 'hygiene fee', rw: 'amafaranga y\'isuku' }

    : { en: 'rent', rw: 'ubukode' };

}



function buildMessages(payment, daysLeft) {

  const amount = formatRwf(payment.amount);

  const due = formatDate(payment.due_date);

  const property = payment.property_name;

  const label = getPaymentLabel(payment.payment_type || 'rent');



  if (daysLeft < 0) {

    const daysOver = Math.abs(daysLeft);

    return {

      title_en: `${label.en === 'rent' ? 'Rent' : 'Hygiene'} Payment Overdue`,

      title_rw: 'Kwishyura byarenze igihe',

      message_en: `Your ${label.en} of ${amount} for ${property} was due on ${due} (${daysOver} day(s) overdue). Please pay as soon as possible.`,

      message_rw: `${label.rw} rwawe ${amount} ku ${property} rwari rukwiye ku wa ${due} (byarenze iminsi ${daysOver}). Wishyure vuba.`,

    };

  }

  if (daysLeft === 0) {

    return {

      title_en: `${label.en === 'rent' ? 'Rent' : 'Hygiene Fee'} Due Today`,

      title_rw: 'Ubu ni umunsi wo kwishyura',

      message_en: `Your ${label.en} of ${amount} for ${property} is due today (${due}). Please make your payment.`,

      message_rw: `${label.rw} rwawe ${amount} ku ${property} rukwiye uyu munsi (${due}). Wishyure.`,

    };

  }

  return {

    title_en: `${label.en === 'rent' ? 'Rent' : 'Hygiene Fee'} Due in ${daysLeft} Day(s)`,

    title_rw: `Kwishyura mu minsi ${daysLeft}`,

    message_en: `Reminder: Your ${label.en} of ${amount} for ${property} is due on ${due} (in ${daysLeft} day(s)).`,

    message_rw: `Ibutumwa: ${label.rw} rwawe ${amount} ku ${property} ruzishyurwa ku wa ${due} (mu minsi ${daysLeft}).`,

  };

}



export async function processPaymentReminders() {

  const payments = await db.prepare(`

    SELECT pay.*, u.id as tenant_user_id, u.email, u.full_name,

           p.name as property_name, t.landlord_id

    FROM payments pay

    JOIN tenants t ON pay.tenant_id = t.id

    JOIN users u ON t.user_id = u.id

    JOIN properties p ON pay.property_id = p.id

    WHERE pay.status IN ('pending', 'overdue')

  `).all();



  const today = new Date();

  today.setHours(0, 0, 0, 0);



  for (const payment of payments) {

    const due = new Date(payment.due_date + 'T00:00:00');

    const daysLeft = Math.round((due - today) / (1000 * 60 * 60 * 24));



    const shouldRemind = daysLeft < 0 || REMINDER_DAYS.includes(daysLeft);

    if (!shouldRemind) continue;



    const reminderKey = getReminderKey(daysLeft);

    const existing = await db.prepare(

      'SELECT payment_id FROM payment_reminder_log WHERE payment_id = ? AND reminder_key = ?'

    ).get(payment.id, reminderKey);

    if (existing) continue;



    const msgs = buildMessages(payment, daysLeft);

    const data = {

      payment_id: payment.id,

      payment_type: payment.payment_type || 'rent',

      amount: payment.amount,

      due_date: payment.due_date,

      property_name: payment.property_name,

      days_left: daysLeft,

      reminder_key: reminderKey,

    };



    const result = await db.prepare(`

      INSERT INTO notifications (user_id, type, title_en, title_rw, message_en, message_rw, data)

      VALUES (?, 'payment_reminder', ?, ?, ?, ?, ?)

    `).run(

      payment.tenant_user_id,

      msgs.title_en,

      msgs.title_rw,

      msgs.message_en,

      msgs.message_rw,

      JSON.stringify(data)

    );



    const label = getPaymentLabel(payment.payment_type || 'rent');

    await db.prepare(`

      INSERT INTO messages (sender_id, receiver_id, property_id, subject, body)

      VALUES (?, ?, ?, ?, ?)

    `).run(

      payment.landlord_id,

      payment.tenant_user_id,

      payment.property_id,

      msgs.title_en,

      `${msgs.message_en}\n\n${msgs.message_rw}`

    );



    const emailSent = await sendEmail({

      to: payment.email,

      subject: `[TenantHub] ${msgs.title_en}`,

      text: `${msgs.message_en}\n\n${msgs.message_rw}\n\n— TenantHub`,

      html: `

        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:24px">

          <h2 style="color:#006fc7">TenantHub — Payment Reminder</h2>

          <p style="color:#334155;font-size:15px">${msgs.message_en}</p>

          <p style="color:#64748b;font-size:14px;border-top:1px solid #e2e8f0;padding-top:12px;margin-top:16px">${msgs.message_rw}</p>

        </div>

      `,

    });



    await db.prepare(

      'INSERT INTO payment_reminder_log (payment_id, reminder_key, email_sent) VALUES (?, ?, ?)'

    ).run(payment.id, reminderKey, emailSent);



    if (emailSent && result.lastInsertRowid) {

      await db.prepare('UPDATE notifications SET email_sent = TRUE WHERE id = ?').run(result.lastInsertRowid);

    }

  }

}


