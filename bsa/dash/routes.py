"""
Main routing module.

This file contains the 'meat 'n' potatoes' as it were. It defines all of the
"subdirectories" of the webserver, as well as the actions required on behalf
of the server whenever one of these pages is accessed.
"""
from .conf import conf
from orm.judge import Judge, JudgeNotFound, JudgeExists
from orm.team import TeamExists

from datetime import datetime
from passlib.hash import bcrypt
import sanic
from sanic import response, exceptions
from sanic_jinja2 import SanicJinja2 as jinja
import uuid


routes = sanic.Blueprint(__name__.split(".")[-1])


def require_auth(redirect=True):
    def decorator(func):
        async def wrapper(request):
            if not request.ctx.session.get('username'):
                if redirect is True:
                    return response.redirect("/login")
                raise exceptions.Forbidden("You are not authorized to access this information.")

            if request.ctx.session.get('ID') != Judge.obtain(request.ctx.session.get('username')).sessionID:
                raise KeyError
            return await func(request)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


@routes.get("/")
@jinja.template("index.html")
async def index_GET(request):
    """Handle GET requests for /."""
    return {}


@routes.get("/login")
@jinja.template("login.html")
async def login_GET(request):
    """Handle GET requests for /login"""
    return {}


@routes.post("/login")
@jinja.template("login.html")
async def login_POST(request):
    """
    Handle POST requests for /login.

    A POST request is sent from /login when the user actually tries to log in.
    Thus, we need to validate their password entry, then redirect them
    to the appropriate page. We also check here to see if a judge is already
    logged in elsewhere, since under this system, we do not permit multiple
    logins, as it could cause data collisions.
    """
    username = request.form['username'][0]
    password = request.form['password'][0]

    try:
        judge = Judge.obtain(username)
    except JudgeNotFound:
        return {'response': f"No user name '{username}' exists."}

    if not bcrypt.verify(password, judge.password):
        return {'response': "Invalid password."}

    if judge.loggedIn:
        return {'response': f"Judge is already logged in elsewhere.\
         If you've just logged out, try waiting {conf.login_timeout} seconds, then try again."}

    request.ctx.session['username'] = judge.username
    request.ctx.session['ID'] = uuid.uuid4().hex
    judge.sessionID = request.ctx.session['ID']
    judge.save()

    try:
        return sanic.response.redirect(request.ctx.session['redirect'])
    except KeyError:
        return sanic.response.redirect("/judge")


@routes.get("/judge")
@jinja.template("judge.html")
@require_auth()
async def judge_GET(request):
    """Handle GET requests for /judge."""
    username = request.ctx.session.get("username")
    judge = Judge.obtain(username)
    return {'judge': judge}


@routes.get("/total")
@jinja.template("total.html")
async def total_GET(request):
    """Handle GET requests for /total"""
    return {'placement': Judge.placement(), 'judges': Judge.obtainall()}


@routes.get("/export")
@jinja.template("export.html")
async def export_GET(request):
    """Handle GET requests for /export"""
    judges = Judge.obtainall()
    team_score_data = {}
    questions = []
    for judge in judges:
        for round_name, round_data in judge.scoretable.items():
            for question, scores in round_data.items():
                if question not in questions:
                    questions.append(question)
                for team, score in scores.items():
                    if team not in team_score_data:
                        team_score_data[team] = {}
                        
                    team_score_data[team][question] = score

    return {'placement': Judge.placement(), 'judges': judges, 'team_scores': team_score_data, 'questions': questions}



@routes.get("/admin")
@jinja.template("admin.html")
async def admin_get(request):
    """Handle GET requests for /admin"""
    if conf.enable_admin_interface:
        judges = Judge.obtainall()
        return {'judges': judges}
    else:
        return sanic.response.text("The admin interface is disabled.")


@routes.post("/admin")
@jinja.template("admin.html")
async def admin_POST(request):
    """Handle POST requests for /admin"""
    if conf.enable_admin_interface is False:
        return sanic.response.text("The admin interface is disabled.")

    username = request.form["username"][0]
    password = bcrypt.hash(request.form["password"][0])
    judges = Judge.obtainall()

    teams = []
    for key, value in request.form.items():
        value = value[0]
        if key.startswith("team"):
            if not value:
                return {'judges': judges, 'response': 'Team names cannot be empty.'}
            teams.append(value)

    if not teams:
        return {'judges': judges, 'response': 'You must specify at least one team per judge.'}

    try:
        Judge.create(username, password, teams)
        return {'judges': judges, 'response': 'Judge successfully created.'}
    except JudgeExists:
        return {'judges': judges, 'response': f"A judge named '{username}' already exists."}
    except TeamExists as e:
        return {'judges': judges, 'response': f"A team named '{e.team}' already exists."}


# Pages prefixed with /api/ are all pages which are not meant to be accessed
# directly. Instead, they allow JS to communicate with the server behind the
# scenes using AJAX.

@routes.get("/api/total")
async def total(request):
    """Handle AJAX requests for /total"""
    return sanic.response.json(Judge.placement())


@routes.post("/api/save-scores")
@require_auth(redirect=False)
async def api_saveScores_POST(request):
    """
    Handle AJAX requests for /judge.

    This handles AJAX requests which are sent whenever a score is saved.
    """
    username = request.ctx.session['username']

    judge = Judge.obtain(username)

    # lol Solomon would *love* this.
    for round, questions in request.json.items():
        for qnumber, answers in questions.items():
            for teamname, answer in answers.items():
                for i, team in enumerate(judge.teams):
                    if team.name == teamname:
                        judge.teams[i].rounds[round][qnumber] = answer
    judge.save()
    return sanic.response.text("success")


@routes.get("/api/update-judge")
async def api_updateJudge_GET(request):
    """Handle AJAX requests for /api/judge-update"""


    judges = {}
    for judge in Judge.obtainall():
        judges[judge.username] = {}
        judges[judge.username]['lastScored'] = f"Q{judge.lastQuestionScored}"
        judges[judge.username]['helpFlag'] = judge.helpFlag
        judges[judge.username]['loggedIn'] = judge.loggedIn

    try:
        username = request.ctx.session['username']
        return sanic.response.json({
            'allUnscored': Judge.allUnscoredQuestions(),
            'judges': judges,
            'helpFlag': Judge.obtain(username).helpFlag
        })
    except KeyError:
        return sanic.response.json({
            'allUnscored': Judge.allUnscoredQuestions(),
            'judges': judges
        })


@routes.post("/api/heartbeat")
@require_auth(redirect=False)
async def api_heartbeat_POST(request):
    username = request.ctx.session['username']
    judge = Judge.obtain(username)
    judge.lastHeartbeat = datetime.now()
    judge.save()
    return sanic.response.text("success")


@routes.post("/api/help-request")
@require_auth(redirect=False)
async def api_helpRequest_POST(request):
    """Handle AJAX requests for /api/help-request"""
    username = request.ctx.session['username']

    judge = Judge.obtain(username)
    judge.helpFlag = request.json['helpFlag']
    judge.save()
    return sanic.response.text("success")


@routes.post("/api/clear-help")
async def api_clearHelp_POST(request):
    """Handle AJAX requests for /api/clear-request"""
    for judge in Judge.obtainall():
        judge.helpFlag = False
        judge.save()
    return sanic.response.text("success")
