# Powered bot by @hackermbrebed

import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)

# Muat variabel lingkungan dari file .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Ambil ID Admin dari .env
ADMIN_USER_ID_STR = os.getenv("ADMIN_USER_ID") 

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- KONFIGURASI GLOBAL (Disimpan dalam memori) ---

GLOBAL_PHOTO_FILE_ID = None 

# Pesan penyambutan dengan format blockquote HTML
WELCOME_MESSAGE = (
    "<blockquote>👋𝙒𝙀𝙇𝘾𝙊𝙈𝙀, {user_name}! 𝙎𝙚𝙡𝙖𝙢𝙖𝙩 𝙗𝙚𝙧𝙜𝙖𝙗𝙪𝙣𝙜 𝙙𝙞 𝙜𝙧𝙪𝙥 𝙠𝙖𝙢𝙞🎉</blockquote>\n\n"
    "╭❈━━━━━━❖ ❖━━━━━━❈╮\n"
    "┣𝐉𝐚𝐧𝐠𝐚𝐧 𝐫𝐞𝐬𝐞𝐤 𝐝𝐚𝐧 𝐢𝐤𝐮𝐭𝐢 𝐫𝐮𝐥𝐞𝐬\n"
    "┣𝐲𝐚𝐧𝐠 𝐚𝐝𝐚!\n"
    "╰❈━━━━━━❖ ❖━━━━━━❈╯\n"
    "╭❈━━━━━━❖ ❖━━━━━━❈╮\n"
    "┣|ɪᴅ ➭  <code>{user_id}</code>\n"
    "┣|ᴜsᴇʀɴᴀᴍᴇ ➭   @{user_username}\n"
    "╰❈━━━━━━❖ ❖━━━━━━❈╯\n\n"
    "<blockquote>𝙎𝙚𝙢𝙤𝙜𝙖 𝙗𝙚𝙩𝙖𝙝!</blockquote>\n"
    "<blockquote>𝘗𝘰𝘸𝘦𝘳𝘦𝘥 𝘣𝘰𝘵 𝘣𝘺 𝕂𝕒𝕚𝕤𝕒𝕣 𝕌𝕕𝕚𝕟👑</blockquote>"
)

# Konfigurasi tombol inline default
GLOBAL_BUTTONS_CONFIG = [
    ['🤖𝙋𝙚𝙢𝙞𝙡𝙞𝙠 𝘽𝙊𝙏', 'https://t.me/udiens123'],
]

# Variabel untuk menampung data tombol sementara saat proses /setbutton
BUTTON_SETUP_DATA = {} 


# ----------------------------------------------------------------------
## FUNGSI UTILITAS DAN PENGECEKAN
# ----------------------------------------------------------------------

def create_inline_keyboard(config):
    """Membuat objek InlineKeyboardMarkup dari list konfigurasi tombol URL."""
    row = []
    for text, action in config:
        if action.startswith('http'):
            row.append(InlineKeyboardButton(text, url=action))
    
    if row:
        return InlineKeyboardMarkup([row]) 

    return None

def admin_private_only(func):
    """Membatasi fungsi hanya untuk ADMIN_USER_ID dan hanya di private chat."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id_int = None
        
        # PERBAIKAN KRITIS: Menggunakan .strip() untuk membersihkan input dari .env
        cleaned_admin_id_str = ADMIN_USER_ID_STR.strip() 

        try:
            admin_id_int = int(cleaned_admin_id_str)
        except (ValueError, TypeError):
             logger.error(f"ADMIN_USER_ID ('{cleaned_admin_id_str}') di file .env tidak valid. Harap gunakan ID numerik.")
             if update.effective_chat.type == 'private':
                 await update.message.reply_text("Kesalahan konfigurasi: ID Admin tidak valid di file .env. Mohon cek log terminal.")
             return
        
        # Log untuk debugging
        logger.info(f"User ID: {update.effective_user.id} | Admin ID Config: {admin_id_int}")

        if update.effective_user.id != admin_id_int:
            if update.effective_chat.type == 'private':
                await update.message.reply_text("Maaf, Anda bukan administrator yang terdaftar.")
            return

        if update.effective_chat.type != 'private':
            await update.message.reply_text("Perintah konfigurasi ini hanya dapat digunakan dalam **private chat** dengan bot.")
            return

        return await func(update, context)
    return wrapper

# ----------------------------------------------------------------------
## HANDLER UTAMA GRUP
# ----------------------------------------------------------------------

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengirim pesan penyambutan saat anggota baru bergabung ke grup."""
    global GLOBAL_PHOTO_FILE_ID, GLOBAL_BUTTONS_CONFIG
    
    logger.info(f"Trigger welcome di chat ID: {update.effective_chat.id}") 

    # Hanya merespons di grup/supergroup
    if update.effective_chat.type not in ['group', 'supergroup']:
        return

    chat = update.effective_chat
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        
        user_id = member.id
        user_name = member.full_name
        user_username = member.username if member.username else '-'

        formatted_message = WELCOME_MESSAGE.format(
            user_name=user_name,
            user_id=user_id,
            user_username=user_username
        )

        reply_markup = create_inline_keyboard(GLOBAL_BUTTONS_CONFIG)
        
        # Logika pengiriman pesan dengan fallback yang andal
        if GLOBAL_PHOTO_FILE_ID:
            try:
                # Coba kirim foto
                await context.bot.send_photo(
                    chat_id=chat.id,
                    photo=GLOBAL_PHOTO_FILE_ID,
                    caption=formatted_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                logger.info(f"Pesan foto welcome berhasil dikirim untuk user {user_id}")
            except Exception as e:
                # FALLBACK: Jika pengiriman foto gagal, kirim pesan teks
                logger.error(f"Gagal mengirim foto: {e}. Mengirim pesan teks sebagai fallback.")
                try:
                    await context.bot.send_message(
                        chat_id=chat.id,
                        text=formatted_message,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as text_e:
                    logger.error(f"Gagal mengirim pesan teks fallback untuk user {user_id}: {text_e}. Abaikan.")
        else:
            # Kirim pesan teks jika tidak ada foto yang diset
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=formatted_message,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                 logger.error(f"Gagal mengirim pesan teks welcome untuk user {user_id}: {e}. Abaikan.")


# ----------------------------------------------------------------------
## HANDLER PERINTAH ADMINISTRATIF (PRIVATE CHAT ONLY)
# ----------------------------------------------------------------------

@admin_private_only
async def set_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mengatur foto penyambutan dari foto yang dibalas (reply)."""
    global GLOBAL_PHOTO_FILE_ID
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("Mohon balas (reply) ke FOTO di chat ini lalu ketik `/setphoto`.")
        return

    photo_file_id = update.message.reply_to_message.photo[-1].file_id
    GLOBAL_PHOTO_FILE_ID = photo_file_id
    
    await update.message.reply_text(
        "✅ Foto penyambutan berhasil diatur!\nFoto ini akan muncul pada sambutan anggota baru.",
        parse_mode='Markdown'
    )

@admin_private_only
async def start_set_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Memulai proses pengaturan tombol inline."""
    user_id = update.effective_user.id
    BUTTON_SETUP_DATA[user_id] = [] 
    context.user_data['setting_buttons'] = True

    await update.message.reply_text(
        "📝 Pengaturan Tombol Inline Dimulai\n\n"
        "Silakan masukkan Nama Tombol dan URL Link pada baris baru.\n"
        "Formatnya adalah: `Nama Tombol Anda URL_LENGKAP`\n"
        "Contoh: `Gabung Grup https://t.me/grupAnda`\n\n"
        "Ketik `/donebutton` saat selesai, atau `/cancelbutton` untuk membatalkan."
    )

@admin_private_only
async def done_set_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menyelesaikan proses pengaturan tombol inline."""
    global GLOBAL_BUTTONS_CONFIG
    user_id = update.effective_user.id
    
    if not context.user_data.get('setting_buttons'):
        await update.message.reply_text("Anda tidak sedang dalam mode pengaturan tombol.")
        return

    new_config = BUTTON_SETUP_DATA.pop(user_id, [])
    
    if not new_config:
        await update.message.reply_text("Tidak ada tombol yang ditambahkan. Konfigurasi tombol tidak diubah.")
        
    else:
        GLOBAL_BUTTONS_CONFIG = new_config
        preview_markup = create_inline_keyboard(GLOBAL_BUTTONS_CONFIG)
        await update.message.reply_text(
            "✅ Tombol inline penyambutan berhasil diubah!\n\nPratinjau:",
            reply_markup=preview_markup,
            parse_mode='Markdown'
        )
        
    context.user_data['setting_buttons'] = False

@admin_private_only
async def cancel_set_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Membatalkan proses pengaturan tombol inline."""
    user_id = update.effective_user.id
    
    if context.user_data.get('setting_buttons'):
        BUTTON_SETUP_DATA.pop(user_id, None)
        context.user_data['setting_buttons'] = False
        await update.message.reply_text("❌ Pengaturan tombol dibatalkan. Konfigurasi lama dipertahankan.")
    else:
        await update.message.reply_text("Anda tidak sedang dalam mode pengaturan tombol.")


@admin_private_only
async def handle_button_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani input teks setelah /setbutton."""
    user_id = update.effective_user.id
    text = update.message.text
    
    if not context.user_data.get('setting_buttons'):
        return

    parts = text.split()
    
    if len(parts) < 2:
        await update.message.reply_text("Format tidak valid. Mohon masukkan minimal dua kata: `Nama Tombol URL`")
        return

    url = parts[-1]
    button_text = " ".join(parts[:-1])

    if not url.startswith(('http://', 'https://', 't.me/')):
        await update.message.reply_text(
            f"❌ Link '{url}' terlihat tidak valid. Pastikan link dimulai dengan `http://`, `https://`, atau `t.me/`."
        )
        return

    BUTTON_SETUP_DATA[user_id].append([button_text, url])
    
    await update.message.reply_text(
        f"✅ Tombol ditambahkan:\nTeks: {button_text}\nLink: `{url}`\n\nTotal tombol: {len(BUTTON_SETUP_DATA[user_id])}. Lanjutkan atau ketik `/donebutton`.",
        parse_mode='Markdown'
    )

@admin_private_only
async def show_current_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan konfigurasi saat ini."""
    global GLOBAL_PHOTO_FILE_ID, GLOBAL_BUTTONS_CONFIG
    
    photo_status = f"ID Foto: `{GLOBAL_PHOTO_FILE_ID}`" if GLOBAL_PHOTO_FILE_ID else "Status: TIDAK ADA FOTO DISIAPKAN"
    
    button_list = "\n".join([f"- {text} -> `{url}`" for text, url in GLOBAL_BUTTONS_CONFIG])
    
    await update.message.reply_text(
        "⚙️ Konfigurasi Bot Saat Ini\n\n"
        "Foto Penyambutan:\n"
        f"{photo_status}\n\n"
        "Tombol Inline:\n"
        f"{button_list}",
        parse_mode='Markdown'
    )


# ----------------------------------------------------------------------
## FUNGSI UTAMA UNTUK MENJALANKAN BOT
# ----------------------------------------------------------------------

def main() -> None:
    """Memulai bot."""
    # Pengecekan Kritis sebelum menjalankan bot
    if not BOT_TOKEN:
        logger.error("Token BOT tidak ditemukan. Bot gagal dijalankan.")
        return
    if 'YOUR_ADMIN_TELEGRAM_ID' in ADMIN_USER_ID_STR:
        logger.error("!!! KESALAHAN KRITIS: ADMIN_USER_ID BELUM DIGANTI di file .env. Bot tidak akan berfungsi untuk konfigurasi. !!!")
        
    try:
        application = Application.builder().token(BOT_TOKEN).build()
    except Exception as e:
        logger.error(f"Gagal membuat aplikasi bot: {e}")
        return

    # Handler Perintah Administrasi (Private Chat Only)
    application.add_handler(CommandHandler("setphoto", set_photo))
    application.add_handler(CommandHandler("setbutton", start_set_button))
    application.add_handler(CommandHandler("donebutton", done_set_button))
    application.add_handler(CommandHandler("cancelbutton", cancel_set_button))
    application.add_handler(CommandHandler("showconfig", show_current_config))
    
    # Handler pesan teks (input tombol)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, handle_button_input
    ))

    # Handler Utama Grup (Welcome Message)
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    logger.info("Bot sedang berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
