import subprocess
import json
import time
import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from moviepy.editor import VideoFileClip
import os
from collections import Counter
import random

def write_recipe(text):
    # Construct the curl command
    curl_command = [
        'curl',
        '--tlsv1.3',
        '--location',
        'https://foodassistantbot.mehrdadmoradi124.workers.dev/',
        '--header', 'Content-Type: application/json',
        '--data', f'{{ "prompt": "{text}" }}'
    ]

    # Execute the curl command and capture output
    result = subprocess.run(curl_command, capture_output=True, text=True)

    response = json.loads(result.stdout)
    return response[0]['response']['response'] #output the actual food dictionary
def choose_grocery(number_of_meals=3): #default is 3 food, each for two days including 4 servings
    final_dict={}
    final_list=[]
    file_dict=open("food.txt","r").readlines()
    file_recipe=open("recipe.txt","r").readlines()
    length=len(file_dict)
    count=0
    while count<3:
        numb=random.randint(0,length-1)
        line_dict=file_dict[numb]
        line_recipe=file_recipe[numb]
        if line_dict['serving']:
            ser=line['serving']
            dic={k: v / ser for k, v in line_dict.iteritems()}
            final_dict=dict(Counter(final_dict) + Counter(dic))
            final_list.append(line_recipe)
            count+=1
    
    final_dict={k: v * 4 for k, v in final_dict.iteritems()}
    final_dict['recipe']=final_list
    return final_dict










import subprocess
import json
from moviepy.editor import VideoFileClip

def video_text(video_path,name):
    # Step 1: Load the video file
    video = VideoFileClip(video_path)
    
    # Step 2: Extract the audio and save it as an MP3 file
    audio_path = "/home/mmoradi6/foodassistant/Audio/"+name+".mp3"
    audio = video.audio
    audio.write_audiofile(audio_path)
    
    # Step 3: Use curl command to send the MP3 file to the Whisper API
    command = f"curl -X POST -F 'file=@{audio_path}' https://wispy-thunder-9516.mehrdadmoradi124.workers.dev/"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Step 4: Store the output in a variable and parse the JSON response
    out = result.stdout
    data = json.loads(out)
    
    # Step 5: Extract the final continuous text
    final_text = data['response']['text']
    
    return final_text




def append_dictionary_to_file(dictionary, filename):
    # Open the file in append mode
    with open(filename, 'a') as file:
        # Convert dictionary to JSON string and write it to the file
        file.write(json.dumps(dictionary))


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Define states
CHOOSE_OPTION, RECIPE, REELS, WEEKLY_GROCERIES, FINISH, SAVE_VIDEO = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation and asks the user to choose an option."""
    reply_keyboard = [['Recipe', 'Reels', 'Weekly Groceries']]

    await update.message.reply_text(
        '<b>Welcome to the foodassistant Bot!\n'
        'What would you like to do today?</b>',
        parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )

    return CHOOSE_OPTION

async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's choice of option."""
    user_choice = update.message.text
    context.user_data['choice'] = user_choice
    logger.info('User choice: %s', user_choice)
    if user_choice == 'Recipe':
        await update.message.reply_text(
            '<b>Please enter the recipe:</b>',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        return RECIPE
    elif user_choice == 'Reels':
        await update.message.reply_text(
            '<b>Please enter the Instagram reels:</b>',
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove()
        )
        return REELS
    elif user_choice == 'Weekly Groceries':

        await update.message.reply_text(

            f'<b>Your weekly grocery list is:\n{choose_grocery()}</b>',
            parse_mode='HTML'
        )
async def recipe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the recipe provided by the user."""
    context.user_data['recipe'] = update.message.text
    out=write_recipe(context.user_data['recipe'])
    append_dictionary_to_file(out, 'food.txt')
    append_dictionary_to_file(context.user_data['recipe'], 'recipe.txt')
    await update.message.reply_text(
        '<b>Recipe noted.</b>',
        parse_mode='HTML'
    )
    return await start(update, context)

async def reels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the video provided by the user."""
    video = update.message.video
    if video:
        # Save video file details in user_data
        file_id = video.file_id
        context.user_data['file_id'] = file_id
        
        # Prompt the user to input a text/name for the video
        await update.message.reply_text(
            "Please provide a name for the video."
        )
        return SAVE_VIDEO
    else:
        await update.message.reply_text(
            "No video found. Please send a video."
        )
        return REELS

async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves the video with the provided name."""
    # Get the provided name from the user
    video_name = update.message.text
    file_id = context.user_data.get('file_id')
    
    if file_id and video_name:
        # Get the video file
        new_file = await context.bot.get_file(file_id)
        
        # Create directory if it doesn't exist
        save_path = "/home/mmoradi6/foodassistant/Video/"
        
        # Create the complete file path with the provided name
        video_path = save_path + video_name + ".mp4"
        
        # Download and save the video file
        await new_file.download_to_drive(video_path)
        text=video_text(video_path,video_name) #save the audio
        write_recipe(text) #add the recipe to the text files
        
        # Respond to the user
        await update.message.reply_text(
            f"Reels noted and saved as {video_name}.mp4. Would you like to summarize or restart?",
            parse_mode='HTML'
        )
        return await start(update, context)
    else:
        await update.message.reply_text(
            "Failed to save the video. Please try again."
        )
        return REELS


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text('Bye! Hope to talk to you again soon.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    application = Application.builder().token("7061065891:AAE7TlkHMWqVTgseYbcSYS_Wk4QWea02Wlo").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSE_OPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_option)],
            RECIPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recipe)],
            REELS: [MessageHandler(filters.VIDEO & ~filters.COMMAND, reels)],
            SAVE_VIDEO: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_video)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('start', start))
    application.run_polling()

if __name__ == '__main__':
    main()
