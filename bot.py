import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.ext import JobQueue
# Configurar el logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("TOKEN")
# Diccionario para almacenar las respuestas de los usuarios
user_responses = {}
# Iniciar el rastreo
tracking = {}
async def start_tracking(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    tracking[user_id] = True
    user_responses[user_id] = []
    await update.message.reply_text("¡Empezando el rastreo! Cada 20 minutos te preguntaré '¿Cómo vamos?'")
    # Configurar la tarea que se repite cada 20 minutos
    job_queue = context.application.job_queue
    job_name = f"track_{user_id}"  # Identificador único del job
    job_queue.run_repeating(track_progress, interval=10, first=0, data=user_id, name=job_name)
async def track_progress(context: CallbackContext) -> None:
    user_id = context.job.data
    await context.bot.send_message(user_id, text="¿Cómo vamos?")
async def end_tracking(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id in user_responses and user_responses[user_id]:
        # Obtener el resumen del día
        responses = "\n".join(user_responses[user_id])
        await update.message.reply_text(f"Resumen del día:\n{responses}")
        # Terminar el rastreo y borrar las respuestas
        tracking[user_id] = False
        user_responses[user_id] = []
        # Detener el job asociado al usuario
        job_name = f"track_{user_id}"
        current_jobs = context.application.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("¡Rastreo terminado!")
    else:
        await update.message.reply_text("No tienes respuestas guardadas, asegúrate de haber usado el bot durante el día.")
# Función para guardar la respuesta
async def save_progress(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in tracking and tracking[user_id]:
        response = update.message.text
        user_responses[user_id].append(response)
        await update.message.reply_text("¡Respuesta guardada!")
    else:
        await update.message.reply_text("Por favor, inicia el rastreo con /empezar primero.")
# Función principal para manejar los comandos
def main() -> None:
    # Crear el Updater y pasarle el TOKEN del bot
    application = Application.builder().token(BOT_TOKEN).build()
    # Añadir los manejadores de comandos
    application.add_handler(CommandHandler("empezar", start_tracking))
    application.add_handler(CommandHandler("acabe", end_tracking))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_progress))
    # Iniciar el bot
    application.run_polling()
if __name__ == '__main__':
    main()