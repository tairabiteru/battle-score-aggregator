# Battle Score Aggregator
A system to automatically count scores for Battle of the Books.

## Why?
Each year, the library I work at hosts an event called Battle of the Books. It's tons of fun, and it's one of the most beloved events that the library runs. BotB is a high-energy event that I liken to going to an amusement park for a day: it's **LOADS** of fun, but you're exhausted by the end of it. Many institutions run similar events, and usually do so in groups of 20 or 30 students. The library I work at however, hosts this event in the local high school drawing crowds of up to 500 people. This makes the event just a *little* bit harder to run. Scoring in particular has always been an issue because it has historically been done on individual laptops in Excel. This is fine, up until the point where the scores have to be totaled. Then there's a scramble to get all of the scores added up and figuring out which judge between four laptops has the highest scoring team.

"That sounds like a job for a computer," I said. But facilitating information transportation between four laptops in a "foreign" network performing a job which absolutely, *positively*, **Can Not Fail** is hard. This program was written to (hopefully) meet that goal and to make scoring not only easier, but instantaneous. The hope is that, by the end of the night, there will be no need to tally scores. We will know the winning team the second the last score is entered.

## Installation
1. Install [poetry](https://python-poetry.org/). This can be done with `python -m pip install poetry` on Linux, or `py -3 -m pip install poetry` on Windows.
2. Clone the repository to a directory of your choice. Then within the repository, run `poetry install`. This will install the project's required dependencies.
3. Start Battle Score Aggregator with `python ./bsa` on Linux, or `py -3 ./bsa` on Windows.

## Usage
The admin interface is enabled by default, as in new installations, the first thing you'd probably want to do is to create new judges, but please note that the admin interface should **NEVER** be enabled in production. It can be disabled in `conf.toml`, once you've created your judges and teams.

Judges can be created by navigating to `http://host:port/admin` where `host` and `port` are the ports specified in `conf.toml`.

Once judges are created, they are considered semi-permanent. They cannot be deleted unless they are quite *literally* deleted from the `/storage` folder. Likewise, if a Judge forgets their password, there is no recourse of action for this. The judge must be created anew.

Once created, a judge can log in with their username and password by navigating to `http://host:port/judge`. Here, the judge may enter scores.

Totals can be found at `http://host:port/total`. Here, the scores and placements of all teams are updated dynamically using AJAX.

## FAQ
- **How do I edit a judge's username?** - There's no way to do this through the web interface. You can however, change the `username` field in their corresponding JSON file in the `/storage` directory. If you do decide to do this, you **MUST** also change the name of the file itself to reflect the new username. Failing to do so will result in errors.

- **How do I change a judge's password?** - You can't. The judge will have to be created anew. You cannot simply edit the password field in the JSON file for the judge because the password is stored in an encrypted format. (Really, if you know how to program and know how to use `passlib` and `bcrypt`, you could do it. But that's above and beyond the scope here.)

- **How do I move teams between judges?** - Okay, this applies pretty much for all questions about changing any information about teams or judges: Judges and teams, once created, are pretty much permanent. Unless you're willing to edit the JSON files, there's no way to change any information about judges through the web interface.

- **How do I delete a judge?** - Delete the judge's corresponding JSON file. There is no way to do this through the web interface by design.

- **Why does the admin interface have to be disabled in production?** - During production when the server is exposed to clients, the admin interface will be accessible to ANYONE who is privy to it. When actually scoring, this is obviously not desirable, as it opens up a massive security hole.

- **Can this be used on the internet?** - Alone, no. The normal operating scenario for this system is for it to be running on a server on a LAN only. In other words, this should NOT be used on the internet, as the internal server is not robust enough for that application.

## Changelog
* Ver 1.1
  - Update Config to be a typehinted dataclass.
  - Switch to newer sanic session library.
  - Add option to export all teams to a CSV file.
* Ver 1.0
  - Minor code refactoring, bump Python version to 3.11, update dependencies. Also release version because I feel like two years of success is enough proof. :)
* Ver. α 1.2
  - Major code refactoring. Ultimately functionality is unchanged though.
* Ver. α 1.1
  - Add the ability to use the arrow keys or `ENTER` to move around the judge's scoring table.
  - Change the `<input>` boxes on the judge's page to be text fields instead of number fields.
  - Fix some rendering issues caused by extreme page width.
  - Correct small rendering issues for Firefox.
  - Update documentation.
* Ver. α 1.0
  - Switch web framework from aiohttp to Sanic. Gotta go fast.
  - Added the ability to easily add custom jinja filters.
    - We don't really need them, but why not?
* Ver. α 0.6
  - Make the help button and scoring key travel down with the scrolling.
  - Show the question AND round on the currently scoring column.
  - Make it so that an "administrator" can respond to a help request and clear it.
  - Fixed a bug which caused scores to render incorrectly on the total export page.
* Ver. α 0.55
  - There is now a scoring key on the Judge's page.
* Ver. α 0.5
  - A team's judge now displays next to the team on the `/total` page.
    - Note that **this is a breaking change**, as the ORM model is now different.
  - Various cosmetic changes.
* Ver. α 0.41
  - Fixed a bug which caused the `/judge` page to not work when certain characters are used in team names.
  - Admin page finally has CSS.
  - Docs updated.
* Ver. α 0.4
  - A judge's status now shows on the `/total` page.
    - ⭕ indicates the judge is not logged in, ⚠️ indicates a judge needs help, and ✔️ indicates they are logged in, and all is good.
  - Added in a help button for judges.
    - When clicked, the button sets a flag which shows a ⚠️ on the `/total` page, as noted above.
  - Implemented session IDs, which makes it impossible for a judge to login in two different places.
  - The `/judge` page now implements a heartbeat protocol.
    - The page will check in with the server as often as it sends updates. If a timeout is exceeded, then the judge is considered 'logged out.'
    - This timeout is configurable in `conf.toml` but should not be set to less than a few seconds.
    - Judges will be prevented from logging in elsewhere if they are not 'logged out.'
* Ver. α 0.31
  - Added some documentation for judges.
* Ver. α 0.3
  - An error message pops up in the event that a judge's session expires, prevents them from entering any more data, and then redirects them to log in.
  - Removed "2" as a valid score.
  - Added the `/export` route to facilitate the following:
    - Made the totals page exportable as a cleaned HTML table.
    - Made it so that the judge's score table can be exported as CSV.
  - Questions are now separated out by round. Configuration options have been added in `conf.toml` to change this.
    - Both the judge and the team ORM models have been changed to facilitate this, so this is a breaking change.
    - In general, this breaks pretty much everything since the last version, so I'd just start over if I were you.
  - Made the table headers on the judge page follow as you scroll down.
  - Indicators on the judge's page now show whether or not all scores have been entered by all judges for a given question.
    - The `/api/update-judge` endpoint has been added to facilitate this.
  - A second column has been added to `/total` which contains the scoring status. This displays the question any judge is currently scoring.
* Ver. α 0.21
  - Fixed a bug which caused the judge's page to render incorrectly.
* Ver. α 0.2
  - Switch the position of the "Add Judge" and "Add Team" buttons.
  - Make it so that a judge cannot be added unless at least one team is added.
  - Make it so that team names cannot be empty.
* Ver. α 0.1
  - Initial commit.

## To-do
- Iunno, prolly some bugs will show up and ruin everything.


## License
[GNU AGPLv3](https://choosealicense.com/licenses/agpl-3.0/)
