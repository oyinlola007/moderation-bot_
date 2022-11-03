import discord, asyncio, warnings, aiohttp
from datetime import datetime
import datetime as dt
from tabulate import tabulate
from dateutil.relativedelta import relativedelta

import cogs.config as config
import cogs.db as db

warnings.filterwarnings("ignore", category=DeprecationWarning)
intents = discord.Intents.all()
client = discord.Client(intents=intents)
client.session = aiohttp.ClientSession()

db.initializeDB()

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

async def timeout_user(*, user_id: int, guild_id: int, until):
    headers = {"Authorization": f"Bot {client.http.token}"}
    url = f"https://discord.com/api/v9/guilds/{guild_id}/members/{user_id}"
    timeout = (datetime.utcnow() + dt.timedelta(minutes=until)).isoformat()
    json = {'communication_disabled_until': timeout}
    async with client.session.patch(url, json=json, headers=headers) as session:
        if session.status in range(200, 299):
           return True
        return False

@client.event
async def on_message(message):
    if not message.author.bot:
        if discord.utils.get(message.author.roles, name=db.get_mod_role()) is not None:
            guild = discord.utils.get(client.guilds, id=config.GUILD_ID)

            if message.content.startswith(";moderate "):
                try:
                    await message.channel.purge(limit=1)

                    if db.count_mod_actions_last_hour(message.author.id) >= db.get_mod_hourly_rate_limit():
                        await message.channel.send("You have reached your hourly rate limit. Please wait until the next hour", delete_after = config.DELETE_AFTER)
                        return

                    #Extract id from message
                    if message.content.startswith(";moderate <@!"):
                        message_content = message.content
                        discord_id = message_content.replace(";moderate <@!", "")
                        discord_id = discord_id.split()[0]
                        discord_id = discord_id.replace(">", "")

                    else:
                        message_content = message.content
                        discord_id = message_content.replace(";moderate ", "")
                        discord_id = discord_id.split()[0]

                    user = await guild.fetch_member(int(discord_id))

                    rules_broken = message_content.split()[2]

                    data = rules_broken.split(",")
                    rules_broken_string = ""
                    for val in data:
                        rules_broken_string += f"Rule <{db.get_rule(val)}>\n"

                    severity = int(message_content.split()[3])
                    proof = message_content.split()[4]

                    duration = db.get_severity(severity)

                    time_stamp = datetime.now().strftime(config.DATE_FORMAT)
                    date_int = datetime.strptime(time_stamp, config.DATE_FORMAT)
                    date_int_after = date_int + relativedelta(minutes=duration)
                    exp = date_int_after.strftime(config.DATE_FORMAT)

                    try:
                        #Checks if user's severity is already at the limit
                        cum_severity = int(db.get_severity_from_severity_table(discord_id))
                        total_severity = cum_severity + severity

                        db.update_severity_point(discord_id, str(total_severity))

                    except:
                        #Creates severity entry if not in db
                        db.insert_severity(discord_id, str(severity), "0", time_stamp)
                        total_severity = severity

                    if total_severity >= db.get_severity_limit():
                        #ban indefinitely
                        await timeout_user(user_id=int(discord_id), guild_id=config.GUILD_ID, until=60*24*7)
                        channel = client.get_channel(db.get_mod_logs_channel())
                        await channel.send(f">>> {user.mention} has been muted indefinitely for breaking the rules. \n\nRules broken:\n{rules_broken_string.strip()}\n\nSeverity: {severity}\n\nProof: {proof}")
                        await message.channel.send(">>> User has been indefinitely muted", delete_after = config.DELETE_AFTER)
                        await user.send(f">>> You have been indefinitely muted for breaking the rules\n\nRules broken:\n{rules_broken_string.strip()}\n\nProof: {proof}")

                        channel = client.get_channel(db.get_ban_review_channel())
                        msg = await channel.send(f">>> <@!{discord_id}> has been muted indefinitely. React with ✅ to ban user from server or ❌ to remove the indefinite mute")
                        await msg.add_reaction("✅")
                        await msg.add_reaction("❌")

                        db.insert_indefinite_muted(discord_id, str(severity), proof)
                        return

                    #mute user for duration
                    await timeout_user(user_id=int(discord_id), guild_id=config.GUILD_ID, until=duration)

                    channel = client.get_channel(db.get_mod_logs_channel())
                    await channel.send(f">>> {user.mention} has been muted till {exp}.\n\nRules broken:\n{rules_broken_string.strip()}\n\nSeverity: {severity}\n\nProof: {proof}")
                    await message.channel.send(f">>> {user.mention} has been muted till {exp}.\n\nRules broken:\n{rules_broken_string.strip()}\n\nSeverity: {severity}", delete_after = config.DELETE_AFTER)
                    await user.send(f">>> {user.mention}, you have been muted till {exp}.\n\nRules broken:\n{rules_broken_string.strip()}\n\nPlease read the rules as you can be banned if your action continues\nYou can contact admin to appeal your muting")

                    db.insert_muted_user(discord_id, str(message.author.id), time_stamp, exp, rules_broken, severity, proof)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content.startswith(";viewmutetime <@!"):
                try:
                    await message.channel.purge(limit=1)
                    #Extract id from message
                    message_content = message.content
                    discord_id = message_content.replace(";viewmutetime <@!", "")
                    discord_id = discord_id.replace(">", "")

                    try:
                        data = db.get_active_muted_user(discord_id)
                        end_time = data[3]
                        start_time = data[2]
                        started = datetime.strptime(start_time, config.DATE_FORMAT)
                        elapsed = datetime.now() - started
                        await message.channel.send(f">>> User has been muted for {elapsed.days} days, {elapsed.seconds//3600} hours, {(elapsed.seconds//60)%60} minutes and {elapsed.seconds%60} seconds. \nTheir mute will expire at {end_time}", delete_after = config.DELETE_AFTER)
                    except:
                        await message.channel.send(f">>> User not currently on mute", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f"Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content.startswith(";setmutetime <@!"):
                try:
                    await message.channel.purge(limit=1)

                    if db.count_mod_actions_last_hour(message.author.id) >= db.get_mod_hourly_rate_limit():
                        await message.channel.send("You have reached your hourly rate limit. Please wait until the next hour", delete_after = config.DELETE_AFTER)
                        return

                    #Extract id from message
                    message_content = message.content
                    discord_id = message_content.replace(";setmutetime <@!", "")
                    discord_id = discord_id.split()[0]
                    discord_id = discord_id.replace(">", "")

                    duration = int(message_content.split()[2])

                    try:
                        data = db.get_active_muted_user(discord_id)
                        start_time = data[2]
                        date_after_month = datetime.today() + relativedelta(minutes=duration)
                        end_time = date_after_month.strftime(config.DATE_FORMAT)
                        db.update_end_time(discord_id, end_time)
                        await message.channel.send(f">>> User mute time set. Their mute will expire at {end_time}", delete_after = config.DELETE_AFTER)

                        #mute user for duration
                        await timeout_user(user_id=int(discord_id), guild_id=config.GUILD_ID, until=duration)
                    except:
                        await message.channel.send(f">>> User not currently on mute", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content.startswith(";viewseveritypoints <@!"):
                try:
                    await message.channel.purge(limit=1)
                    #Extract id from message
                    message_content = message.content
                    discord_id = message_content.replace(";viewseveritypoints <@!", "")
                    discord_id = discord_id.replace(">", "")

                    data = db.get_severity_table(discord_id)
                    try:
                        severity = data[1]
                        expired_severity = data[2]
                        await message.channel.send(f">>> User has {severity} severity points and {expired_severity} expired severity points", delete_after = config.DELETE_AFTER)
                    except:
                        await message.channel.send(f">>> User has no severity points", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

        if discord.utils.get(message.author.roles, name=db.get_admin_role()) is not None:
            if message.content.startswith(";viewmodstats <@!"):
                try:
                    await message.channel.purge(limit=1)
                    #Extract id from message
                    message_content = message.content
                    discord_id = message_content.replace(";viewmodstats <@!", "")
                    discord_id = discord_id.replace(">", "")

                    muted_count = db.count_mod_muted(discord_id, "30 days")
                    banned_count = db.count_mod_banned(discord_id, "30 days")
                    report_count = db.count_mod_reports(discord_id, "30 days")
                    forgive_count = db.count_mod_removed_indefinite_mute(discord_id, "30 days")
                    await message.channel.send(f">>> <@!{discord_id}>:\n-muted {muted_count} users\n-banned {banned_count} users\n-attended to {report_count} reports\n-removed {forgive_count} users from indefinite mute", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content.startswith(";setseveritypoints <@!"):
                try:
                    await message.channel.purge(limit=1)
                    #Extract id from message
                    message_content = message.content
                    discord_id = message_content.replace(";setseveritypoints <@!", "")
                    discord_id = discord_id.split()[0]
                    discord_id = discord_id.replace(">", "")

                    amount = int(message_content.split()[2])

                    try:
                        db.update_severity_point(discord_id, str(amount))
                    except:
                        await message.channel.send(f">>> User has no severity points", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content.startswith(";setting "):
                try:
                    await message.channel.purge(limit=1)
                    #Extract id from message
                    setting = message.content.split()[1]
                    value = message.content.split()[2]

                    db.update_variable(setting, value)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

            elif message.content == ";settings":
                try:
                    await message.channel.purge(limit=1)

                    data = [["SETTINGS", "CURRENT VALUE"]]

                    for row in db.get_variables():
                        data.append([row[0], row[1]])

                    table = tabulate(data, headers="firstrow")
                    await message.channel.send(f"```{table}```", delete_after = config.DELETE_AFTER)

                except Exception as e:
                    await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)


        if message.content.startswith(";report <@!"):
            try:
                await message.channel.purge(limit=1)
                #Extract id from message
                message_content = message.content
                discord_id = message_content.replace(";report <@!", "")
                discord_id = discord_id.split()[0]
                discord_id = discord_id.replace(">", "")

                reason = message_content.split(">")[1]

                channel = client.get_channel(db.get_reports_channel())
                msg = await channel.send(f">>> <@!{message.author.id}> has reported <@!{discord_id}> \n\nReason: {reason}")
                await msg.add_reaction(config.REACTION_EMOJI)

            except Exception as e:
                await message.channel.send(f">>> Error occurred- {e}", delete_after = config.DELETE_AFTER)

        try:
            if message.content == "!get_db":
                await message.channel.send(file=discord.File(config.DATABASE_NAME))
        except:
            pass

@client.event
async def on_reaction_add(reaction, user):
    guild = discord.utils.get(client.guilds, id=config.GUILD_ID)
    if not user.bot:
        if discord.utils.get(user.roles, name=db.get_mod_role()) is not None:
            if reaction.emoji == config.REACTION_EMOJI and user.id != config.BOT_ID and reaction.message.channel.id == db.get_reports_channel():
                try:
                    if db.count_mod_actions_last_hour(user.id) >= db.get_mod_hourly_rate_limit():
                        await user.send(">>> You have reached your hourly rate limit. Please wait until the next hour", delete_after = config.DELETE_AFTER)
                        return

                    reporter = reaction.message.content.split("<@!")[1].split(">")[0]
                    reported = reaction.message.content.split("<@!")[2].split(">")[0]
                    reason = reaction.message.content.split("\n\nReason: ")[1]
                    moderator = str(user.id)
                    time_stamp = datetime.now().strftime(config.DATE_FORMAT)
                    await reaction.message.delete()
                    channel = client.get_channel(db.get_mod_logs_channel())
                    await channel.send(f">>> <@!{reported}> has been reported\n\nReason: {reason}\n\nModerator: <@!{moderator}>")
                    db.insert_report(reporter, reported, reason, moderator, time_stamp)
                except:
                    pass

            elif user.id != config.BOT_ID and reaction.message.channel.id == db.get_ban_review_channel():

                if db.count_mod_actions_last_hour(user.id) >= db.get_mod_hourly_rate_limit():
                    await user.send(">>> You have reached your hourly rate limit. Please wait until the next hour", delete_after = config.DELETE_AFTER)
                    return

                if reaction.emoji == "✅":
                    try:
                        discord_id = reaction.message.content.split("<@!")[1].split(">")[0]
                        moderator = str(reaction.message.author.id)
                        time_stamp = datetime.now().strftime(config.DATE_FORMAT)
                        await reaction.message.delete()
                        channel = client.get_channel(db.get_mod_logs_channel())
                        await channel.send(f">>> <@!{discord_id}> has been banned\n\nModerator: <@!{moderator}>")

                        user = await guild.fetch_member(int(discord_id))
                        await user.ban(reason="User violated server rules")

                        db.delete_from_indefinite_mute(discord_id)
                        db.insert_banned(discord_id, moderator, time_stamp)
                    except:
                        pass

                elif reaction.emoji == "❌":
                    try:
                        discord_id = reaction.message.content.split("<@!")[1].split(">")[0]
                        moderator = str(reaction.message.author.id)
                        time_stamp = datetime.now().strftime(config.DATE_FORMAT)
                        await reaction.message.delete()
                        channel = client.get_channel(db.get_mod_logs_channel())
                        await channel.send(f">>> <@!{discord_id}> is no longer indefinitely muted\n\nModerator: <@!{moderator}>")

                        await timeout_user(user_id=int(discord_id), guild_id=config.GUILD_ID, until=1)
                        db.delete_from_indefinite_mute(discord_id)
                        db.insert_removed_indefinite_mute(discord_id, moderator, time_stamp)
                    except:
                        pass

async def user_metrics_background_task():
    await client.wait_until_ready()
    while True:
        guild = discord.utils.get(client.guilds, id=config.GUILD_ID)

        #Loops through all muted users
        for row in db.get_active_muted_users():
            try:
                discord_id, end_time = row[0], row[3]
                expiry_date = datetime.strptime(end_time, config.DATE_FORMAT)

                if expiry_date < datetime.now():
                    user = await guild.fetch_member(int(discord_id))

                    db.update_muted_status(discord_id)
                    await user.send(f">>> Your mute has expired. Please read the rules as you can be banned if your action continues")

            except Exception as e:
                pass
                #member = await guild.fetch_member(config.ADMIN_ID)
                #await member.send(f"```Error occurred\n\n{e}```")

        #Loops through all severities
        for row in db.get_all_severity():
            try:
                discord_id, severity, expired_severity, check_point = row[0], int(row[1]), int(row[2]), row[3]

                check_point = datetime.strptime(check_point, config.DATE_FORMAT)
                elapsed = datetime.now() - check_point

                if severity != 0:
                    #don't bother if severity is 0
                    if elapsed.days >= db.get_severity_expire_duration():
                        severity -= 1
                        expired_severity += 1
                        time_stamp = datetime.now().strftime(config.DATE_FORMAT)
                        db.update_severity_table(discord_id, str(severity), str(expired_severity), time_stamp)

            except Exception as e:
                pass
                #member = await guild.fetch_member(config.ADMIN_ID)
                #await member.send(f"```Error occurred\n\n{e}```")

        #Loops through all indefinite muted
        for row in db.get_active_muted_users():
            try:
                discord_id = row[0]
                await timeout_user(user_id=int(discord_id), guild_id=config.GUILD_ID, until=60*24*7)
            except:
                pass

        for i in range(10):
            await asyncio.sleep(1)

client.loop.create_task(user_metrics_background_task())
client.run(config.DISCORD_TOKEN)





























