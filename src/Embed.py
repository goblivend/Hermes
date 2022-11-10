import discord

from src.ConfigFormat import Config


def urlButton(url: str):
    return discord.ui.Button(label="Link", style=discord.ButtonStyle.link, url=url)


class ReopenView(discord.ui.View):
    @discord.ui.button(label="Reopen", style=discord.ButtonStyle.green, emoji="🔓")
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):
        thread = interaction.channel
        forum = thread.parent
        config = Config("config/config.yaml")
        config_forum = config.get_forum(forum.id)
        if not config_forum:
            await interaction.response.send_message("Forum not found", ephemeral=True)
            return
        if interaction.user.id not in config.settings.managers and interaction.user.id != thread.owner.id:
            await interaction.response.send_message("You are not allowed to do that", ephemeral=True)
            return
        for tag in forum.available_tags:
            if tag.name == config_forum.end_tag:
                await thread.remove_tags(tag)
                break

        await thread.edit(archived=False, locked=False)
        await interaction.message.delete()
        await interaction.response.send_message("Reopened", ephemeral=True)
        log_chan = interaction.client.get_channel(config_forum.webhook_channel)

        await thread.edit(auto_archive_duration=10080)  # 7 days to archive
        embed = newThreadEmbed(thread)
        view = discord.ui.View()
        view.add_item(urlButton(thread.jump_url))
        await log_chan.send(embed=embed, view=view)


def strTag(tag: discord.ForumTag):
    s = f"**{tag.name}**"
    if tag.emoji:
        s += f" {tag.emoji}"
    return s


def newThreadEmbed(thread: discord.Thread, reopened=False):
    embed = discord.Embed(title=thread.name, color=discord.Color.orange())
    if thread.starter_message:
        embed.description = thread.starter_message.content
    embed.timestamp = thread.created_at
    if reopened:
        embed.add_field(name="Status", value="Open 🟢")  # must be fist field
    else:
        embed.add_field(name="Status", value="Reopened 🟢")  # must be fist field
    embed.set_author(name=thread.owner.display_name, icon_url=thread.owner.display_avatar)
    if thread.applied_tags:
        embed.add_field(name="Tags", value="\n".join([strTag(tag) for tag in thread.applied_tags]))

    embed.set_footer(text=f"Thread ID: {thread.id}")
    return embed


def doneEmbed(member: discord.Member, status: str):
    embed = discord.Embed(title="Ticket has been closed by an assistant", color=discord.Color.blue())
    if status == "Duplicate":
        embed.colour = discord.Colour.red()
        embed.title = "This question has already been answered. Please check if your question is already answered " \
                      "before creating a new ticket."

    embed.set_author(name=member.display_name, icon_url=member.display_avatar)  # TODO: change name to server name
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text="If you have any further questions, please create a new ticket.")
    return embed


def editEmbed(embed: discord.Embed, member: discord.Member, status: str):
    if status == "Resolved":
        embed.set_field_at(0, name="Status", value="Done ✅")
        embed.colour = discord.Colour.light_gray()
    elif status == "Duplicate":
        embed.set_field_at(0, name="Status", value="Duplicate 🟡")
        embed.colour = discord.Colour.gold()
    elif status == "Closed":
        embed.set_field_at(0, name="Status", value="Closed 🔴")
        embed.colour = discord.Colour.red()
    elif status == "Joined":
        embed.set_field_at(0, name="Status", value="Joined 🟢")
        embed.colour = discord.Colour.orange()

    for field in embed.fields:
        if field.name == "Action done by":
            embed.remove_field(embed.fields.index(field))
            break
    embed.add_field(name="Action done by", value=member.mention)

    embed.timestamp = discord.utils.utcnow()


def newTicketEmbed(student: discord.Member,login: str, question: str, channel: discord.TextChannel):
    embed = discord.Embed(title="New ticket created", color=discord.Color.orange())
    embed.description = question
    embed.set_author(name=student.display_name, icon_url=student.display_avatar)
    embed.add_field(name="Login", value=login)
    embed.timestamp = discord.utils.utcnow()
    embed.set_footer(text=f"Channel ID: {channel.id}")
    return embed
