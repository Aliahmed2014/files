import os
import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='+', intents=intents)

member_price = 500
receiver_id = 1289256703509921944
stock_role_id = 1069611840910413874
owner_id = 1289256703509921944

stock = 0
pending_payments = {}

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def buy_member(ctx, quantity: int = None):
    global stock
    if quantity is None or quantity <= 0:
        await ctx.send('❌ الرجاء تحديد الكمية بشكل صحيح. مثال: `+buy_member 3`')
        return

    if stock < quantity:
        await ctx.send(f'❌ العدد المطلوب غير متوفر. المخزون الحالي: {stock}')
        return

    if ctx.author.id in pending_payments:
        await ctx.send('❗ لديك طلب شراء معلق، انتظر الأونر.')
        return

    total_price = quantity * member_price
    stock -= quantity

    # إرسال رسالة التحويل والتعليمات
    await ctx.send(f'#credit {receiver_id} {total_price}')
    await ctx.send(
        f'✅ لديك 3 دقائق لتحويل الكريدت ({total_price} كريدت).\n'
        f'⏳ تم استلام الطلب. الرجاء الانتظار حتى يأتي الأونر.'
    )

    # حفظ الطلب
    pending_payments[ctx.author.id] = {
        'quantity': quantity,
        'total_price': total_price,
        'channel': ctx.channel,
        'task': None,
        'confirmed': False
    }

    async def timeout_task():
        await asyncio.sleep(180)
        if ctx.author.id in pending_payments and not pending_payments[ctx.author.id]['confirmed']:
            await ctx.channel.send(f'⏰ <@{ctx.author.id}> انتهى الوقت. لم تتم أي عملية دفع.')
            global stock
            stock += quantity
            del pending_payments[ctx.author.id]

    task = bot.loop.create_task(timeout_task())
    pending_payments[ctx.author.id]['task'] = task

@bot.command(name='تم-التحويل')
async def confirm_transfer(ctx):
    if ctx.author.id not in pending_payments:
        await ctx.send('❌ لا يوجد طلب شراء مسجل باسمك.')
        return

    pending_payments[ctx.author.id]['confirmed'] = True
    await ctx.send('✅ تم استلام التحويل بنجاح، انتظر الأونر يأتي.')

@bot.command(name='شراء-أعضاء')
async def verify(ctx, status: str = None):
    if ctx.author.id != owner_id:
        await ctx.send('❌ هذه الأوامر خاصة بالأونر فقط.')
        return
    if not pending_payments:
        await ctx.send('ℹ️ لا توجد طلبات شراء حالياً.')
        return

    user_id, info = next(iter(pending_payments.items()))
    if status == 'تم':
        info['task'].cancel()
        del pending_payments[user_id]
        await ctx.send('✅ تم تأكيد الدفع.')
        await info['channel'].send(f'✅ <@{user_id}> تم تأكيد الدفع، شكرًا لك!')
    elif status == 'لم':
        info['task'].cancel()
        stock += info['quantity']
        del pending_payments[user_id]
        await ctx.send('❌ لم يتم الدفع.')
        await info['channel'].send(f'❌ <@{user_id}> لم يتم الدفع.')
    else:
        await ctx.send('❗ استخدم: `+شراء-أعضاء تم` أو `+شراء-أعضاء لم`')

@bot.command()
@commands.has_role(stock_role_id)
async def addstock(ctx, amount: int = None):
    global stock
    if amount is None or amount <= 0:
        await ctx.send('❌ حدد عدد صحيح.')
        return
    stock += amount
    await ctx.send(f'✅ أضفت {amount}. المخزون الحالي: {stock}')

@addstock.error
async def on_add_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send('🚫 لا تملك صلاحيات!')

@bot.command(name='stock')
async def show_stock(ctx):
    await ctx.send(f'📦 عدد الأعضاء في المخزون هو: {stock}')

bot.run(os.getenv('DISCORD_TOKEN'))
