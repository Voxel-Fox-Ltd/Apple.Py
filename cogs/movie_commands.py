import typing

import discord
from discord.ext import commands, vbu


class MovieCommand(vbu.Cog):

    async def send_omdb_query(self, name: str, media_type: str, search: bool, year = None) -> dict:
        """
        Send a query to the OMDB API, returning the results dict.
        """

        # Build up the params
        key = 's' if search else 't'
        params = {
            'apikey': self.bot.config['api_keys']['omdb'],
            'type': media_type,
            key: name,
        }
        if year:
            params.update({'year': year})
        headers = {"User-Agent": self.bot.user_agent}

        # Send the request
        async with self.bot.session.get("http://www.omdbapi.com/", params=params, headers=headers) as r:
            data = await r.json()
        return data

    def generate_embed(self, data) -> typing.Optional[vbu.Embed]:
        """
        Make an embed based on some OMDB data.
        """

        search = data.get('Title') is None
        if search and data.get('Search') is None:
            return None

        embed = vbu.Embed(use_random_colour=True)
        if not search:
            embed.title = f"{data['Title']} ({data['Year']})"

        valid_info = lambda v: v not in [None, 'N/A', 'n/a']

        # List short details of up to 10 results
        if search:
            description_list = []
            for index, row in enumerate(data['Search'][:10], start=1):
                if valid_info(row.get('Poster')):
                    description_list.append(f"{index}. **{row['Title']}** ({row['Year']}) - [Poster]({row['Poster']})")
                else:
                    description_list.append(f"{index}. **{row['Title']}** ({row['Year']})")
            embed.description = '\n'.join(description_list)
            return embed

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
            embed.add_field(f"Genre{'s' if ',' in data['Genre'] else ''}", data['Genre'])
        if data.get('imdbRating'):
            embed.add_field("IMDB Rating", data['imdbRating'])
        if data.get('Production'):
            embed.add_field(f"Production Compan{'ies' if ',' in data['Production'] else 'y'}", data['Production'])
        if data.get('Director'):
            embed.add_field(f"Director{'s' if ',' in data['Director'] else ''}", data['Director'])
        if data.get('Writer'):
            embed.add_field(f"Writer{'s' if ',' in data['Writer'] else ''}", data['Writer'], inline=False)
        if data.get('imdbID'):
            embed.add_field("IMDB Page", f"[Direct Link](https://www.imdb.com/title/{data['imdbID']}/) - IMDB ID `{data['imdbID']}`", inline=False)
        if valid_info(data.get('Poster')):
            embed.set_thumbnail(data['Poster'])
        return embed

    @commands.group(
        invoke_without_command=True,
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'omdb')
    async def movie(self, ctx: vbu.Context):
        """
        The parent command for movie commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @movie.group(
        name="get",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    description="The name of the movie that you want to get.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="year",
                    description="The year that the movie was released.",
                    type=discord.ApplicationCommandOptionType.integer,
                    min_value=1800,
                    max_value=2100,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'omdb')
    async def movie_get(self, ctx: vbu.Context, *, name: str, year: int = None):
        """
        Gets a movie from the OMDB API.
        """

        # Try and return the found data
        data = await self.send_omdb_query(name,'movie',False,year)
        embed = self.generate_embed(data)
        if not embed:
            return await ctx.send(
                f"Couldn't find any results for **{name}**",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        return await ctx.send(embed=embed)

    # @movie.group(name="search")
    # @commands.bot_has_permissions(send_messages=True, embed_links=True)
    # @vbu.checks.is_config_set('api_keys', 'omdb')
    # async def movie_search(self, ctx: vbu.Context, *, name: str):
    #     """
    #     Searches for a movie on the OMDB API.
    #     """

    #     # See if we gave a year
    #     original_name = name
    #     if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
    #         *name, year = name.split(' ')
    #         name = ' '.join(name)
    #     else:
    #         year = None

    #     # Try and return the found data
    #     await ctx.defer()
    #     data = await self.send_omdb_query(name,'movie',True,year)
    #     embed = self.generate_embed(data)
    #     if not embed:
    #         return await ctx.send(f"No movie results for `{original_name}` could be found.", allowed_mentions=discord.AllowedMentions.none())
    #     return await ctx.send(embed=embed)

    @commands.group(
        invoke_without_command=True,
        application_command_meta=commands.ApplicationCommandMeta(),
    )
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'omdb')
    async def tv(self, ctx: vbu.Context):
        """
        The parent group for the TV commands.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @tv.command(
        name="get",
        application_command_meta=commands.ApplicationCommandMeta(
            options=[
                discord.ApplicationCommandOption(
                    name="name",
                    description="The name of the TV show that you want to get.",
                    type=discord.ApplicationCommandOptionType.string,
                ),
                discord.ApplicationCommandOption(
                    name="year",
                    description="The year that the TV show was released.",
                    type=discord.ApplicationCommandOptionType.integer,
                    min_value=1800,
                    max_value=2100,
                ),
            ],
        ),
    )
    @commands.defer()
    @commands.bot_has_permissions(send_messages=True, embed_links=True)
    @vbu.checks.is_config_set('api_keys', 'omdb')
    async def tv_get(self, ctx: vbu.Context, *, name: str, year: int = None):
        """
        Gets a TV show from the OMDB API.
        """

        # Try and return the found data
        data = await self.send_omdb_query(name, 'series', False, year)
        embed = self.generate_embed(data)
        if not embed:
            return await ctx.send(
                f"Couldn't find any results for **{name}**",
                allowed_mentions=discord.AllowedMentions.none(),
            )
        return await ctx.send(embed=embed)

    # @tv.command(name="search")
    # @commands.bot_has_permissions(send_messages=True, embed_links=True)
    # @vbu.checks.is_config_set('api_keys', 'omdb')
    # async def tv_search(self, ctx: vbu.Context, *, name: str):
    #     """
    #     Searches for a TV series on the OMDB API.
    #     """

    #     # See if we gave a year
    #     original_name = name
    #     if name.split(' ')[-1].isdigit() and int(name.split(' ')[-1]) > 1900:
    #         *name, year = name.split(' ')
    #         name = ' '.join(name)
    #     else:
    #         year = None

    #     # Try and return the found data
    #     await ctx.defer()
    #     data = await self.send_omdb_query(name, 'series', True, year)
    #     embed = self.generate_embed(data)
    #     if not embed:
    #         return await ctx.send(f"No TV series results for `{original_name}` could be found.", allowed_mentions=discord.AllowedMentions.none())
    #     return await ctx.send(embed=embed)


def setup(bot: vbu.Bot):
    x = MovieCommand(bot)
    bot.add_cog(x)
