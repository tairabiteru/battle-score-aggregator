from dash.conf import conf
from .team import Team, TeamSchema, TeamExists

from datetime import datetime
import json
from marshmallow import Schema, fields, post_load
import os


if not os.path.exists(conf.storage_directory):
    os.makedirs(conf.storage_directory)


class JudgeNotFound(Exception):
    """Raised when a judge does not exist."""
    pass


class JudgeExists(Exception):
    """Raised when a judge by the specified name already exists."""
    pass


class JudgeSchema(Schema):
    username = fields.Str()
    password = fields.Str()
    teams = fields.List(fields.Nested(TeamSchema))
    helpFlag = fields.Boolean()
    lastHeartbeat = fields.DateTime(allow_none=True)
    sessionID = fields.Str()


    @post_load
    def make_obj(self, data, **kwargs):
        return Judge(**data)


class Judge:
    """
    Define a judge.

    Stores the username, the password (hashed and salted) and a list of
    teams the judge is responsible for.
    """

    def __init__(self, **kwargs):
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.teams = kwargs['teams'] if 'teams' in kwargs else []
        self.helpFlag = kwargs['helpFlag'] if 'helpFlag' in kwargs else False
        self.lastHeartbeat = kwargs['lastHeartbeat'] if 'lastHeartbeat' in kwargs else None
        self.sessionID = kwargs['sessionID'] if 'sessionID' in kwargs else ""

    @classmethod
    def obtain(cls, username):
        """
        Obtain a judge given the username.

        If no judge is found, JudgeNotFound is raised.
        """
        try:
            filename = os.path.join(conf.storage_directory, f"{username.lower()}.json")
            with open(filename, 'r', encoding='utf-8') as file:
                return JudgeSchema().load(json.load(file))
        except FileNotFoundError:
            raise JudgeNotFound

    @classmethod
    def obtainall(cls):
        """Obtain all judges."""
        judges = []
        for file in os.listdir(conf.storage_directory):
            filename = os.path.join(conf.storage_directory, file)
            with open(filename, 'r', encoding='utf-8') as file:
                judges.append(JudgeSchema().load(json.load(file)))
        return judges

    @classmethod
    def allUnscoredQuestions(cls):
        unscored = []
        for judge in cls.obtainall():
            for question in judge.unscoredQuestions():
                if question not in unscored:
                    unscored.append(question)
        return sorted(unscored, key=lambda x: int(x))

    @classmethod
    def create(cls, username, password, teamnames):
        """
        Create a judge.

        Takes their username, password, and a list of team names they will be
        responsible for. Team objects are created dynamically.
        """
        try:
            judge = cls.obtain(username.lower())
            raise JudgeExists
        except JudgeNotFound:
            pass

        teams = []
        for teamname in teamnames:
            if teamname.lower() in list([team.name.lower() for team in cls.allTeams()]):
                raise TeamExists(teamname)
            teams.append(Team(name=teamname, judge=username))

        judge = Judge(username=username, password=password, teams=teams)
        judge.save()
        return judge

    @classmethod
    def allTeams(cls):
        """Get a list of all teams."""
        judges = cls.obtainall()
        teams = []
        for judge in judges:
            teams += judge.teams
        return teams

    @classmethod
    def questionIsDone(cls, question):
        """Determines if scoring is pending or final."""
        return not any([q[question] == "" for q in cls.allTeams()])


    @classmethod
    def placement(cls):
        """
        Obtain the 'placement' of all teams.

        This is used when rendering the total scores.
        """
        teams = cls.allTeams()
        placement = {}
        place = 1
        while len(teams) != 0:
            team_placement = {}
            highest = max([team.total for team in teams])
            while max([team.total for team in teams]) == highest:
                for team in teams:
                    if team.total == highest:
                        team_placement[team.name] = {'total': team.total, 'judge': team.judge.capitalize()}
                        teams.remove(team)
                if teams == []:
                    break
            placement[str(place)] = team_placement
            place += 1
        return placement

    @property
    def lastQuestionScored(self):
        return min(list(map(int, self.unscoredQuestions())))

    @property
    def loggedIn(self):
        if not self.lastHeartbeat:
            return False
        delta = datetime.now() - self.lastHeartbeat
        return delta.total_seconds() < conf.login_timeout

    @property
    def scoretable(self):
        """
        Obtain scoretable.

        The scoretable is an enumerated set of question numbers and the
        stored scores associated with each team. It is used to render the
        judge's scoring page.
        """
        rounds = {}
        for r, questions in self.teams[0].rounds.items():
            round = {}
            for number, score in questions.items():
                question = {}
                for team in self.teams:
                    question[team.name] = team.rounds[r][number]
                round[number] = question
            rounds[r] = round
        return rounds

    def unscoredQuestions(self):
        unscored = []
        for team in self.teams:
            for round, questions in team.rounds.items():
                for qnumber, answer in questions.items():
                    if answer == "" and qnumber not in unscored:
                        unscored.append(qnumber)
        return unscored

    def save(self):
        """Save to JSON."""
        try:
            os.makedirs(conf.storage_directory)
        except FileExistsError:
            pass
        filename = os.path.join(conf.storage_directory, f"{self.username}.json")
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(JudgeSchema().dump(self), file, indent=4, separators=(',', ': '))
