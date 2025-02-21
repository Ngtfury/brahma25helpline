import json
import time
import telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sys
from pathlib import Path

from dotenv import load_dotenv
import os 

load_dotenv()

TOKEN= os.getenv('TOKEN')

sys.path.append("/home/teknikal/Desktop/HC EVENTS/telegram bot")
#from config import TOKEN

# File paths using Path for better cross-platform compatibility
DATA_DIR = Path("./data")
FILES = {
    "general": DATA_DIR / "general.json",
    "cultural": DATA_DIR / "cultural.json",
    "technical": DATA_DIR / "technical.json",
    "results": DATA_DIR / "results.json",
    "stats": DATA_DIR / "bot_stats.json"  
}

# Ensure stats file exists
def initialize_stats_file():
    stats_file = FILES["stats"]
    if not stats_file.exists():
        default_stats = {
            "total_users": 0,
            "unique_users": set(),  
            "start_time": time.time(),
            "downtime_periods": [],
            "commands_used": {
                "start": 0,
                "event_details": 0,
                "contact_team": 0,
                "results": 0,
                "bot_status": 0
            }
        }
        with open(stats_file, 'w') as f:
            # Convert set to list for JSON serialization
            stats_copy = default_stats.copy()
            stats_copy["unique_users"] = list(stats_copy["unique_users"])
            json.dump(stats_copy, f)
    return

# Update bot stats
def update_stats(user_id, command):
    try:
        stats_file = FILES["stats"]
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        
        # Convert unique_users back to set for processing
        stats["unique_users"] = set(stats["unique_users"])
        
        # Update stats
        stats["total_users"] += 1
        stats["unique_users"].add(str(user_id))
        if command in stats["commands_used"]:
            stats["commands_used"][command] += 1
        
        # Convert set back to list for JSON storage
        stats["unique_users"] = list(stats["unique_users"])
        
        with open(stats_file, 'w') as f:
            json.dump(stats, f)
    except Exception as e:
        print(f"Error updating stats: {e}")

WELCOME_MESSAGE = """
🎉 *Brahma'25 helpline Bot!* 🎉

I'm here to assist you with Brahma'25😊.
How can I help you today?
"""

COORDINATOR_MESSAGE = """
👥 *Brahma'25 Organizing Team*

Select a team to view their details:
"""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    update_stats(user_id, "start")
    
    keyboard = [
        [InlineKeyboardButton("📅 Event Details", callback_data='day_selection')],
        [InlineKeyboardButton("🕗 Event Timeline", callback_data='event_timeline')],
        [InlineKeyboardButton("👥 Contact Team", callback_data='coordinators')],
        [InlineKeyboardButton("🏆 Event Results", callback_data='results')],
        [InlineKeyboardButton("📊 Bot Status", callback_data='bot_status')],
        [InlineKeyboardButton("👨‍💻 Developer Info", callback_data='developers')]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=reply_markup, parse_mode='Markdown')

async def timeline_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle day selection for timeline view."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🗓️ Day 1 (Feb 28)", callback_data='timeline_Day 1')],
        [InlineKeyboardButton("🗓️ Day 2 (Mar 01)", callback_data='timeline_Day 2')],
        [InlineKeyboardButton("🗓️ Day 3 (Mar 02)", callback_data='timeline_Day 3')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📅 *Select a day to view the timeline:*", reply_markup=reply_markup, parse_mode='Markdown')

def get_all_events_by_time(day: str) -> dict:
    """Fetch and combine events from all categories for a specific day, sorted by time."""
    all_events = {}
    
    # Categories to check
    categories = ['general', 'cultural', 'technical']
    
    for category in categories:
        file_path = FILES.get(category)
        if file_path and file_path.exists():
            try:
                with open(file_path, "r") as file:
                    events = json.load(file)
                    # Filter events for the specific day
                    day_events = [event for event in events if event["EVENT DATE"] == day]
                    
                    # Group events by time
                    for event in day_events:
                        time_slot = event["EVENT TIMES"]
                        if time_slot not in all_events:
                            all_events[time_slot] = []
                        all_events[time_slot].append(event["EVENT NAME"])
            except (json.JSONDecodeError, FileNotFoundError):
                continue
    
    # Convert times to 24-hour format for sorting
    def time_to_24hr(time_str):
        try:
            # Parse time like "9:00 AM" or "02:30 PM"
            time_obj = time.strptime(time_str, "%I:%M %p")
            return time.strftime("%H:%M", time_obj)
        except:
            return "00:00"  # Default value for invalid times
    
    # Sort by converted 24-hour time
    sorted_events = dict(sorted(all_events.items(), 
                              key=lambda x: time_to_24hr(x[0])))
    
    return sorted_events

async def show_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display the timeline for the selected day."""
    query = update.callback_query
    await query.answer()
    
    day = query.data.split('_')[1]
    events_by_time = get_all_events_by_time(day)
    
    if events_by_time:
        message = f"📅 Timeline for {day}\n\n"
        
        for time_slot, events in events_by_time.items():
            message += f"*{time_slot}*\n"
            for event in events:
                message += f"• {event}\n"
            message += "\n"
    else:
        message = f"No events scheduled for {day} yet!"
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Days", callback_data='event_timeline')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')

async def day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    update_stats(user_id, "event_details")
    
    keyboard = [
        [InlineKeyboardButton("🗓️ Day 1 (Feb 28)", callback_data='Day 1')],
        [InlineKeyboardButton("🗓️ Day 2 (Mar 01)", callback_data='Day 2')],
        [InlineKeyboardButton("🗓️ Day 3 (Mar 02)", callback_data='Day 3')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📅 *Which day would you like to explore?*", reply_markup=reply_markup, parse_mode='Markdown')

async def events_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day = query.data
    
    keyboard = [
        [InlineKeyboardButton("🎭 Cultural Events", callback_data=f'cultural_{day}')],
        [InlineKeyboardButton("🌐 General Events", callback_data=f'general_{day}')],
        [InlineKeyboardButton("🔧 Technical Events", callback_data=f'technical_{day}')],
        [InlineKeyboardButton("🔙 Back to Days", callback_data='day_selection')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        f"🎯 *What type of events interest you for {day}?*", 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def get_events(category: str, day: str) -> list:
    """Fetch events from JSON file based on category and day."""
    file_path = FILES.get(category)
    if not file_path or not file_path.exists():
        return []
    
    try:
        with open(file_path, "r") as file:
            events = json.load(file)
        return [event for event in events if event["EVENT DATE"] == day]
    except (json.JSONDecodeError, FileNotFoundError):
        return []

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category, day = query.data.split('_', 1)
    events = get_events(category, day)
    
    try:
        if events:
            keyboard = [
                [InlineKeyboardButton(f"📌 {event['EVENT NAME']}", 
                callback_data=f'details_{category}_{event["EVENT NAME"]}')] 
                for event in events
            ]
            keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data=f'Day {day[-1]}')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                f"🎪 *Available {category.capitalize()} Events - {day}:*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            await query.message.edit_text(
                "😅 No events scheduled for this day yet!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f'Day {day[-1]}')]])
            )
    except telegram.error.BadRequest as e:
        print(f"Error in show_events: {e}")
        # If we can't edit, try sending a new message
        if "There is no text in the message to edit" in str(e):
            try:
                # Delete old message if possible
                try:
                    await query.message.delete()
                except:
                    pass
                
                # Send as new message
                if events:
                    keyboard = [
                        [InlineKeyboardButton(f"📌 {event['EVENT NAME']}", 
                        callback_data=f'details_{category}_{event["EVENT NAME"]}')] 
                        for event in events
                    ]
                    keyboard.append([InlineKeyboardButton("🔙 Back to Categories", callback_data=f'Day {day[-1]}')])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"🎪 *Available {category.capitalize()} Events - {day}:*",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                else:
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text="😅 No events scheduled for this day yet!",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=f'Day {day[-1]}')]])
                    )
            except Exception as new_e:
                print(f"Failed to send new message: {new_e}")    


async def show_event_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    _, category, event_name = query.data.split('_', 2)
    
    file_path = FILES.get(category)
    if not file_path or not file_path.exists():
        try:
            await query.message.edit_text(
                "❌ Event details not available.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='day_selection')]])
            )
        except telegram.error.BadRequest:
            # If edit fails, send new message
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ Event details not available.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='day_selection')]])
            )
        return
    
    try:
        with open(file_path, "r") as file:
            events = json.load(file)
        
        event = next((e for e in events if e["EVENT NAME"] == event_name), None)
        
        if event:
            event_day = event["EVENT DATE"]
            
            response = f"""
<b>EVENT DETAILS</b>

<b>🎯 Event:</b> {event["EVENT NAME"]}
<b>📍 Venue:</b> {event["VENUE"]}
<b>⏰ Time:</b> {event["EVENT TIMES"]}


<b>REGISTRATION DETAILS</b>

🔗 <b>Link:</b> <a href="{event["LINK"]}">Register Here</a>  
💸 <b>Fees:</b> {event["FEES"]}  
🙋‍♂️ <b>Spot Registration:</b> {event["SR"]}  


<b>👥 EVENT COORDINATORS</b>  
{event["C1"]}  
{event["C2"]}

            """
            
            # Create back button to return to events list
            back_callback = f'{category}_{event_day}'
            keyboard = [[InlineKeyboardButton("🔙 Back to Events", callback_data=back_callback)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Always delete old message and send new one - most reliable approach
            try:
                await query.message.delete()
            except Exception as del_e:
                print(f"Could not delete message: {del_e}")
            
            if "IMAGE" in event and event["IMAGE"]:
                try:
                    await context.bot.send_photo(
                        chat_id=query.message.chat_id,
                        photo=event["IMAGE"],
                        caption=response,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as img_e:
                    print(f"Error sending image: {img_e}")
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=response,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            else:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=response,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        else:
            try:
                await query.message.edit_text(
                    "❌ Event not found.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='day_selection')]])
                )
            except telegram.error.BadRequest:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="❌ Event not found.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='day_selection')]])
                )
    except Exception as e:
        print(f"Error in show_event_details: {e}")
        try:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="❌ An error occurred while retrieving event details.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]])
            )
        except Exception as inner_e:
            print(f"Failed to send error message: {inner_e}")


async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the back to main menu button."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📅 Event Details", callback_data='day_selection')],
        [InlineKeyboardButton("🕗 Event Timeline", callback_data='event_timeline')],
        [InlineKeyboardButton("👥 Contact Team", callback_data='coordinators')],
        [InlineKeyboardButton("🏆 Event Results", callback_data='results')],
        [InlineKeyboardButton("📊 Bot Status", callback_data='bot_status')],
        [InlineKeyboardButton("👨‍💻 Developer Info", callback_data='developers')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(WELCOME_MESSAGE, reply_markup=reply_markup, parse_mode='Markdown')

async def show_coordinators(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the coordinators menu."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    update_stats(user_id, "contact_team")
    
    keyboard = [
        [InlineKeyboardButton("👥 Student Coordination", callback_data='coord_student')],
        [InlineKeyboardButton("📝 Registration Team", callback_data='coord_registration')],
        [InlineKeyboardButton("🍽️ Refreshment Team", callback_data='coord_refreshment')],
        [InlineKeyboardButton("🏥 Medical Team", callback_data='coord_medical')],
        [InlineKeyboardButton("👮 Discipline Team", callback_data='coord_discipline')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        COORDINATOR_MESSAGE,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def show_team_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display specific team details."""
    query = update.callback_query
    await query.answer()
    
    team_type = query.data.split('_')[1]
    
    team_messages = {
        #student coordination team
                'student': """
*Student Coordination Team* 👥 

_Coordinators:_
 ```Nandhitha```  +917304396216
```Vyshak```  +919745913185

For student related queries, please contact the above team.
        """,

    #registeration team
        'registration': """
*Registration Team* 📝

_Coordinators:_
```Alen``` +919744134203
```Devanandha``` +919037604721

For registration related queries, please contact the above team.
        """,

    #refreshments team
        'refreshment': """
*Refreshment Team* 🍽️ 

_Coordinators:_
```Harikrishnan``` +919446990681
```Vivek``` +919747737337

For refreshment related queries, please contact the above team.
        """,

    #medical team    
        'medical': """
🏥 *Medical Team*

_Emergency Contacts:_ 
```Aleena``` +9181039026386
```Devika``` +918590282983

For any medical assistance/emergency during the event, please contact the above team.
        """,

        #discipline team
        'discipline': """
*Discipline Team*👮 

_Coordinators:_
```Dhrupath``` +919400941004
```Yadhu``` +918138835700

For any discipline related concerns, please contact the above team.
        """
    }
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Teams", callback_data='coordinators')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        team_messages.get(team_type, "Team details not available"),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def results_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    update_stats(user_id, "results")
    
    keyboard = [
        [InlineKeyboardButton("🗓️ Day 1 (Feb 28)", callback_data='results_Day 1')],
        [InlineKeyboardButton("🗓️ Day 2 (Mar 01)", callback_data='results_Day 2')],
        [InlineKeyboardButton("🗓️ Day 3 (Mar 02)", callback_data='results_Day 3')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("🏆 *Select the day to view event results:*", reply_markup=reply_markup, parse_mode='Markdown')

async def show_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display bot status and statistics."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    update_stats(user_id, "bot_status")
    
    try:
        with open(FILES["stats"], 'r') as f:
            stats = json.load(f)
        
        # Calculate uptime
        current_time = time.time()
        uptime_seconds = current_time - stats["start_time"]
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format uptime
        uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        # Get downtime information
        downtime_count = len(stats["downtime_periods"])
        total_downtime = sum([period["end"] - period["start"] for period in stats["downtime_periods"]], 0)
        downtime_hours = total_downtime / 3600 if total_downtime else 0
        
        # Create status message
        status_message = f"""
📊 *BOT STATUS REPORT*

👥 *Usage Statistics:*
• Total Interactions: {stats["total_users"]}
• Unique Users: {len(stats["unique_users"])}

⏱️ *Uptime:*
• Bot Running Since: {uptime_str}
• Downtime Incidents: {downtime_count}
• Total Downtime: {downtime_hours:.2f} hours

📈 *Command Usage:*
• Start: {stats["commands_used"]["start"]}
• Event Details: {stats["commands_used"]["event_details"]}
• Contact Team: {stats["commands_used"]["contact_team"]}
• Results: {stats["commands_used"]["results"]}
• Status Checks: {stats["commands_used"]["bot_status"]}

⚡ *Current Status:* ONLINE
        """
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            status_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error displaying bot status: {e}")
        await query.message.edit_text(
            "❌ Error retrieving bot statistics. Please try again later.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data='start')]]),
            parse_mode='Markdown'
        )

def record_downtime(is_down=True):
    """Record bot downtime periods."""
    try:
        with open(FILES["stats"], 'r') as f:
            stats = json.load(f)
        
        current_time = time.time()
        
        if is_down:
            # Start recording downtime
            stats["downtime_periods"].append({"start": current_time, "end": None})
        else:
            # End the latest downtime period if it exists
            if stats["downtime_periods"] and stats["downtime_periods"][-1]["end"] is None:
                stats["downtime_periods"][-1]["end"] = current_time
        
        with open(FILES["stats"], 'w') as f:
            json.dump(stats, f)
    except Exception as e:
        print(f"Error recording downtime: {e}")
async def show_developers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    dev_message = """

*DEVELOPERS:*
 `Brian Roy Mathew`

*CONTRIBUTORS*
 `Ashwin P Shine`
 `Chandra Rajesh`
 `Deepak M.R.`
 `Anandhakrishnan`
 `Ceeya Sarah Varghese`


_Developed & Handled with ❤️ by HackClub ASIET_
    """
    
    keyboard = [
        [InlineKeyboardButton("Connect with Team", callback_data='connection')],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data='start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(dev_message, reply_markup=reply_markup, parse_mode='Markdown')

async def show_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    dev_message = """
    Connect With Us:

📍[BRIAN ROY MATHEW](https://www.linkedin.com/in/brianroymathew/)
📍[ASHWIN P SHINE](https://www.linkedin.com/in/ashwin-p-shine/)
📍[CHANDRA RAJESH](https://www.linkedin.com/in/chandra-rajesh/)
📍[DEEPAK M.R.](https://www.linkedin.com/in/deepak-m-r-ab601a291/)
📍[ANANTHAKRISHNAN](https://www.google.com)
📍[CEEYA SARAH VARGHESE](https://www.linkedin.com/in/ceeya-sarah-varghese-38280632a/)
    """

    keyboard = [[InlineKeyboardButton("🔙 Back to Developer Info", callback_data='developers')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(dev_message, reply_markup=reply_markup, parse_mode='Markdown')


def main():
    """Initialize and run the bot."""
    print("🤖 BRAHMA'25 BOT: ONLINE")
    
    # Initialize the stats file if it doesn't exist
    initialize_stats_file()
    
    # Record that the bot is online (end any previous downtime)
    record_downtime(is_down=False)
    
    # Create the application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CallbackQueryHandler(day_selection, pattern='^day_selection$'))
    app.add_handler(CallbackQueryHandler(events_menu, pattern='^Day [1-3]$'))
    app.add_handler(CallbackQueryHandler(show_events, pattern='^(cultural|general|technical)_Day [1-3]$'))
    app.add_handler(CallbackQueryHandler(show_event_details, pattern='^details_.*'))
    app.add_handler(CallbackQueryHandler(show_coordinators, pattern='^coordinators$'))
    app.add_handler(CallbackQueryHandler(show_team_details, pattern='^coord_.*'))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern='^start$'))
    app.add_handler(CallbackQueryHandler(results_day_selection,pattern='^results$'))
    app.add_handler(CallbackQueryHandler(show_bot_status, pattern='^bot_status$'))
    app.add_handler(CallbackQueryHandler(timeline_day_selection, pattern='^event_timeline$'))
    app.add_handler(CallbackQueryHandler(show_timeline, pattern='^timeline_Day [1-3]$'))
    app.add_handler(CallbackQueryHandler(show_developers, pattern='^developers$'))
    app.add_handler(CallbackQueryHandler(show_connection, pattern='^connection$'))

    
    print("✅ BOT IS READY TO ASSIST WITH BRAHMA'25 NAVIGATION")
    
    try:
        app.run_polling()
    except Exception as e:
        print(f"Bot crashed with error: {e}")
        # Record that the bot is down
        record_downtime(is_down=True)
        raise e

if __name__ == '__main__':
    main()