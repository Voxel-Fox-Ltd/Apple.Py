import discord
from discord.ext import commands
import voxelbotutils as utils


class MovieCommand(utils.Cog):

    @utils.group(invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def movie(self, ctx:utils.Context, *, name:str):
        """Searches for a movie on the OMDB API"""

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        # Build up the params
        params = {
            'apikey': self.bot.config['api_keys']['omdb'],
            't': name,
            'type': 'movie'
        }
        if year:
            params.update({'year': year})

        # Send the request
        async with self.bot.session.get("http://www.omdbapi.com/", params=params) as r:
            data = await r.json()

        # Build an embed
        if data.get('Title') is None:
            return await ctx.invoke(self.bot.get_command("movie search"), name=original_name)
        with utils.Embed(use_random_colour=True, title=f"{data['Title']} ({data['Year']})") as embed:
            if data['Plot']:
                embed.description = data['Plot']
            if data['Released']:
                embed.add_field("Release Date", data['Released'])
            if data['Rated']:
                embed.add_field("Age Rating", data['Rated'])
            if data['Runtime']:
                embed.add_field("Runtime", data['Runtime'])
            if data['Genre']:
                embed.add_field("Genre", data['Genre'])
            if data['imdbRating']:
                embed.add_field("IMDB Rating", data['imdbRating'])
            if data['Production']:
                embed.add_field("Production Company", data['Production'])
            if data['Director']:
                embed.add_field("Director", data['Director'])
            if data['Writer']:
                embed.add_field("Writer", data['Writer'], inline=False)
            if data['imdbID']:
                embed.add_field("IMDB Page", f"[Direct Link](https://www.imdb.com/title/{data['imdbID']}/) - IMDB ID `{data['imdbID']}`", inline=False)
            if data['Poster']:
                embed.set_thumbnail(data['Poster'])
        return await ctx.send(embed=embed)

    @movie.group()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def search(self, ctx:utils.Context, *, name:str):
        """Searches for a movie on the OMDB API"""

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        # Build up the params
        params = {
            'apikey': self.bot.config['api_keys']['omdb'],
            's': name,
            'type': 'movie'
        }
        if year:
            params.update({'year': year})

        # Send the request
        async with self.bot.session.get("http://www.omdbapi.com/", params=params) as r:
            data = await r.json()

        # See if we got anything
        if data.get('Search') is None:
            return await ctx.send(f"No movie results for `{original_name}` could be found.", allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

        # Build an embed
        embed = utils.Embed(use_random_colour=True)
        description_list = []
        for index, row in enumerate(data['Search'][:10], start=1):
            if row['Poster']:
                description_list.append(f"{index}. **{row['Title']}** ({row['Year']}) - [Poster]({row['Poster']})")
            else:
                description_list.append(f"{index}. **{row['Title']}** ({row['Year']})")
        embed.description = '\n'.join(description_list)
        return await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = MovieCommand(bot)
    bot.add_cog(x)
