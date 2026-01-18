# Chat Commands

## 1. Dota 2

<table>
  <tr>
    <th>Command Name</th>
    <th class="aliases-column">Chat Aliases</th>
    <th>Description</th>
    <th>Showcase (<a href="https://7tv.app/emote-sets/01JS1XW1PAAKP34984FDYZVDR7">7tv emote set</a> on)</th>
  </tr>
  <tr>
    <td>Game Medals</td>
    <td class="aliases-column">!gm</td>
    <td>
      Show rank medal for each players in the match.
    </td>
    <td><img src="./images/gm.png" alt="gm" width="1200"/></td>
  </tr>
  <tr>
    <td>Lifetime Games</td>
    <td class="aliases-column">!smurfs<br/>!lifetime</td>
    <td>
      Show total games played for each player in the match.
    </td>
    <td><img src="./images/lifetime.png" alt="lifetime" width="1200"/></td>
  </tr>
  <tr>
    <td>Live Match Player Stats</td>
    <td class="aliases-column">!stats<br/>!items<br/>!kda</td>
    <td>
      Fetch live stats and items for a player in the current match (2 minutes delay).
      Note, you need to provide an argument for the command such as hero name, hero alias, player slot or player color.
      I.e. "!stats pa", "!stats blue", "!stats mireska", "!stats Templar Assassin".
    </td>
    <td><img src="./images/stats.png" alt="stats" width="1200"/></td>
  </tr>
  <tr>
    <td>Player Stats Profiles</td>
    <td class="aliases-column">!profile<br/>!player</td>
    <td>
      Show link to stats profile for a player.
      Similarly to above, you need to provide an argument for the command such as hero name, alias; player slot or color.
    </td>
    <td><img src="./images/player.png" alt="player" width="1200"/></td>
  </tr>
  <tr>
    <td>Notable players</td>
    <td class="aliases-column">!notable<br/>!np</td>
    <td>
      Show notable players in the match.
      This includes streamers, twitch chatters and pro-players.
      Honestly, everybody is welcome to be added as a notable player.
    </td>
    <td><img src="./images/notable.png" alt="notable" width="1200"/></td>
  </tr>
  <tr>
    <td>Ranked</td>
    <td class="aliases-column">!ranked</td>
    <td>
      Show whether the current match is ranked or not.
    </td>
    <td><img src="./images/ranked.png" alt="ranked" width="1200"/></td>
  </tr>
  <tr>
    <td>Match ID</td>
    <td class="aliases-column">!match_id<br/>!matchid</td>
    <td>
      Show match id for the current game.
    </td>
    <td><img src="./images/matchid.png" alt="matchid" width="1200"/></td>
  </tr>
  <tr>
    <td>Played with in Last Game</td>
    <td class="aliases-column">!lg<br/>!lm<br/>!played</td>
    <td>
      Show recurring players from the last game present in the current game.
    </td>
    <td><img src="./images/last-game.png" alt="last-game" width="1200"/></td>
  </tr>
  <tr>
    <td>Previous Match Results</td>
    <td class="aliases-column">!pm</td>
    <td>
      Show a short summary for the previous match results.
    </td>
    <td><img src="./images/pm.png" alt="pm" width="1200"/></td>
  </tr>
  <tr>
    <td>Win Loss Ratio</td>
    <td class="aliases-column">!wl<br/>!score<br/>!winloss</td>
    <td>
      Show streamer's win-loss score ratio during the live-stream.
    </td>
    <td><img src="./images/score.png" alt="score" width="1200"/></td>
  </tr>
  <tr>
    <td>Offline Win Loss Ratio</td>
    <td class="aliases-column">!wl offline</td>
    <td>
      Show win-loss ratio for the last streamer's gaming session but also include offline games.
    </td>
    <td><img src="./images/score.png" alt="score" width="1200"/></td>
  </tr>
  <tr>
    <td>MMR</td>
    <td class="aliases-column">!mmr</td>
    <td>
      Show streamer's mmr tracked in the bot database (according to their match history).
      It is not accurate.
    </td>
    <td><img src="./images/mmr.png" alt="mmr" width="1200"/></td>
  </tr>
  <tr>
    <td>Set MMR</td>
    <td class="aliases-column">!mmr set</td>
    <td>
      (Streamer's only command) Allows for streamers to manually update their MMR in the bot's database.
    </td>
    <td><img src="./images/mmr-set.png" alt="mmr-set" width="1200"/></td>
  </tr>
  <tr>
    <td>Stats Profile</td>
    <td class="aliases-column">!dotabuff<br/>!stratz<br/>!opendota</td>
    <td>
      Show link to the streamer's stats profile page.
    </td>
    <td><img src="./images/dotabuff.png" alt="dotabuff" width="1200"/></td>
  </tr>
  <tr>
    <td>Last Seen</td>
    <td class="aliases-column">!lastseen</td>
    <td>
      Show which account the bot has spotted you playing Dota 2 last on.
      The bot considers this account as "active" for the purposes of the commands above.
    </td>
    <td><img src="./images/lastseen.png" alt="lastseen" width="1200"/></td>
  </tr>
  <tr>
    <td>D2PT Hero Builds</td>
    <td class="aliases-column">!d2pt</td>
    <td>
      Show Dota 2 ProTracker page for the currently selected hero.
    </td>
    <td><img src="./images/d2pt.png" alt="d2pt" width="1200"/></td>
  </tr>
</table>

### Tip for merging 7tv emote sets

To make bot responses look like in the "Showcase" column you can add those emotes quickly to your channel by merging your main 7tv emote set with the <a href="https://7tv.app/emote-sets/01JS1XW1PAAKP34984FDYZVDR7">Dota 2 emote set</a> using a tool like [potat.app/help/mergeset](<https://potat.app/help/mergeset>). Some short instructions for @PotatBotat specifically:

* Add @PotatBotat to your channel;
* Give it 7tv editor role, allow it to `Create Emote Sets` in addition to default permissions;
* Use `#mergeset <Primary set ID> 01JS1XW1PAAKP34984FDYZVDR7` where the second argument is an ID for the mentioned Dota 2 emote set;
* You can find your `<Primary set ID>` by copying the last part of the URL to your own main emote set;
* @PotatBotat will create a new emote set trying to merge the provided ones; if there is more then 1000 emotes in total - some emotes from the 2nd set won't make it;
* Now you can switch between your main set and a merged version;

### Dota 2 bot functionality restrictions

Unfortunately, due to implementation specifics currently for Dota 2 features to work:

  1. You need to add the bot's steam accounts to friends.
  2. You also need to be green-online 🟢 in Dota 2 (and have rich presence visible to friends) for the bot to be able to see your status live.

PS. Another implementation for these features (using Dota 2 Game State Integration) is coming soon™️. It won't have mentioned restrictions but you will have to put a `.cfg` file into the Dota 2 directory.

## 2. Meta

<table>
  <tr>
    <th>Command Name</th>
    <th class="aliases-column">Chat Aliases</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>Commands List</td>
    <td class="aliases-column">!commands<br/>!help<br/>!irenesbot</td>
    <td>Show link to this page.</td>
    <tr>
    <td>Source Code</td>
    <td class="aliases-column">!source<br/>!github</td>
    <td><a href="https://github.com/Aluerie/IreBot">github.com/Aluerie/IreBot</a></td>
  </tr>
  </tr>
  <tr>
    <td>Irene</td>
    <td class="aliases-column">!irene</td>
    <td><img src="./images/FeelsDankMan.png" alt="FeelsDankMan" width="64"/></td>
  </tr>
</table>
