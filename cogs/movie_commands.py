import discord
from discord.ext import commands
import voxelbotutils as utils


class MovieCommand(utils.Cog):

    async def omdb_query(self, name, mediatype, search, year=None):
        # Build up the params
        key = 's' if search else 't'
        params = {
            'apikey': self.bot.config['api_keys']['omdb'],
            key: name,
            'type': mediatype
        }
        if year:
            params.update({'year': year})
        headers = {"User-Agent": self.bot.user_agent}

        # Send the request
        async with self.bot.session.get("http://www.omdbapi.com/", params=params, headers=headers) as r:
            data = await r.json()
        return data
    
    def generate_embed(self,data):
        search = data.get('Title') is None
        
        if search and data.get('Search') is None:
            return None

        if search:
            embed = utils.Embed(use_random_colour=True)
        else:
            embed = utils.Embed(use_random_colour=True, title=f"{data['Title']} ({data['Year']})")
        
        if search:
            # List short details of up to 10 results
            description_list = []
            for index, row in enumerate(data['Search'][:10], start=1):
                if row['Poster']:
                    description_list.append(f"{index}. **{row['Title']}** ({row['Year']}) - [Poster]({row['Poster']})")
                else:
                    description_list.append(f"{index}. **{row['Title']}** ({row['Year']})")
            embed.description = '\n'.join(description_list)
        else:
            # List full details
            if data.get('Plot'):
                embed.description = data['Plot']
            if data.get('Released'):
                embed.add_field("Release Date", data['Released'])
            if data.get('Rated'):
                embed.add_field("Age Rating", data['Rated'])
            if data.get('Runtime'):
                embed.add_field("Runtime", data['Runtime'])
            if data.get('Genre'):
                embed.add_field("Genre", data['Genre'])
            if data.get('imdbRating'):
                embed.add_field("IMDB Rating", data['imdbRating'])
            if data.get('Production'):
                embed.add_field("Production Company", data['Production'])
            if data.get('Director'):
                embed.add_field("Director", data['Director'])
            if data.get('Writer'):
                embed.add_field("Writer", data['Writer'], inline=False)
            if data.get('imdbID'):
                embed.add_field("IMDB Page", f"[Direct Link](https://www.imdb.com/title/{data['imdbID']}/) - IMDB ID `{data['imdbID']}`", inline=False)
            if data.get('Poster'):
                embed.set_thumbnail(data['Poster'])
        return embed

    @utils.group(invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def movie(self, ctx:utils.Context, *, name:str):
        """
        Searches for a movie on the OMDB API.
        """

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        data = await self.omdb_query(name,'movie',False,year)

        embed = self.generate_embed(data)

        if not embed:
            return await ctx.invoke(self.bot.get_command("movie search"), name=original_name)

        return await ctx.send(embed=embed)

    @movie.group(name="search")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def movie_search(self, ctx:utils.Context, *, name:str):
        """
        Searches for a movie on the OMDB API.
        """

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        data = await self.omdb_query(name,'movie',True,year)

        embed = self.generate_embed(data)

        if not embed:
            return await ctx.send(f"No movie results for `{original_name}` could be found.", allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

        return await ctx.send(embed=embed)

    @utils.group(invoke_without_command=True)
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def tv(self, ctx:utils.Context, *, name:str):
        """
        Searches for a TV series on the OMDB API
        """

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        data = await self.omdb_query(name,'series',False,year)

        embed = self.generate_embed(data)

        if not embed:
            return await ctx.invoke(self.bot.get_command("tv search"), name=original_name)
        
        return await ctx.send(embed=embed)
    
    @tv.group(name="search")
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @utils.checks.is_config_set('api_keys', 'omdb')
    async def tv_search(self, ctx:utils.Context, *, name:str):
        """
        Searches for a TV series on the OMDB API.
        """

        # See if we gave a year
        original_name = name
        if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
            *name, year = name.split(' ')
            name = ' '.join(name)
        else:
            year = None

        data = await self.omdb_query(name,'series',True,year)

        embed = self.generate_embed(data)

        if not embed:
            return await ctx.send(f"No TV series results for `{original_name}` could be found.", allowed_mentions=discord.AllowedMentions(users=False, roles=False, everyone=False))

        return await ctx.send(embed=embed)


def setup(bot:utils.Bot):
    x = MovieCommand(bot)
    bot.add_cog(x)
