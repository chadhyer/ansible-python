help_text = """
Grafana API key generator

This script allows the user to generate an API key to the specified api_key_file location.
The api key requires an organization to be created and associated with the API Key.

The scripts names the API key the org name with '_apikey' appended to the end.

A key will not be generated if one already exists at the provided file path (-f --file)
and the key name matches the provided org name else the script will attempt to generate
a new API key with the provided arguments.

Technically multiple API keys can be generated if you specify unique org and file arguments.
Note that once an API key has been generated it will no longer be accessible if not stored 
properly.

Arguments:
    -h --help       Display this help text

    -f --file       File path to store api key (Required Argument)
                    Default: None 

    -H --host       Host of the grafana server
                    Default: localhost

    -P --port       Port the grafana server is hosted
                    Default: 3000

    -u --user       Username for grafana server
                    Default: admin

    -p --pass       Password for grafana user
                    Default: admin

    -o --org        Organization name API will be generated for
                    Default: trusted
"""

from sys import exit, argv
from pathlib import Path
import requests
import json


class MissingArgumentError(Exception):
    """Exception raised for missing arguments"""

    def __init__(self, argument_list:list):
        self.message = f'Missing argument! {argument_list=}!'
        super().__init__(self.message)


class InvalidUsernameOrPasswordError(Exception):
    """Exception raised for username or password errors when interacting with 
    the grafana api"""

    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)


class CreateAPITokenError(Exception):
    """Exception raised for api token generation errors"""

    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)


class OrganizationError(Exception):
    """Exception raised for issues relating to grafana organization"""

    def __init__(self, message:str):
        self.message = message
        super().__init__(self.message)


def help_() -> None:
    """Simply print help text"""
    print(help_text)


def check_arguments(name:str, user:str, password:str, 
                    host:str, port:int, api_key_file:Path) -> None:
    """
    Returns None if arguments are holding values else raises 
        MissingArgumentError exception

        Parameters:
            name (str): Name for the new organization
            user (str): User for grafana (typically admin)
            password (str): Password for the grafana user
            host (str): Host for the grafana server
            port (int): Port for the grafana server
        
        Returns:
            None: no issues found and arguments are populated
            MissingArgumentError exception if arguments are None
    """
    argument_list = [ name, user, password, host, host, port, api_key_file ]
    index = 0
    for argument in argument_list:
        var = [key for key, value in locals().items() if value == argument]
        if isinstance(argument, type(None)):
            raise MissingArgumentError(var)

        index += 1


def check_api_key_file(name:str, api_key_file:Path) -> bool:
    """
    Returns True if an api_key exists and False if the api_key is missing

        Parameters:
            name (str): Name associated with the api key
            api_key_file (Path): Path leading to the file storing the API key

        Returns:
            True: api key exists in api_key_file with associated name key
            False: api key is missing or associated name is different
    """
    if api_key_file.exists():
        with open(api_key_file, 'r') as file:
            try:
                data = json.load(file)
            except json.decoder.JSONDecodeError:
                data = {}
            if "key" in data and "name" in data:
                if data['name'] == f'{name}':
                    return True
    return False


def create_api_token(name:str, user:str, password:str, 
                     host:str, port:int) -> dict:
    """
    Returns API token generated using the provided org_id

        Parameters:
            name (str): Name for the apikey
            user (str): User for grafana (typically admin)
            password (str): Password for the grafana user
            host (str): Host for the grafana server
            port (int): Port for the grafana server
        Returns:
            key (dict): API key generated with keys, 'id', 'key', and 'name'
            None: If there was an issue generating API key
    """

    json_data = {
        'name': f'{name}',
        'role': 'Admin',
    }

    access = f'http://{user}:{password}@{host}:{port}'
    url = access + '/api/auth/keys'

    response = requests.post(url, json=json_data)

    data = json.loads(str(response.content, 'utf-8'))

    if "message" in data:
        raise CreateAPITokenError(data['message'])

    if "key" in data:
        return data


def post_org(name:str, user:str, password:str, host:str, port:int) -> int:
    '''
    Returns integer of orgId if the org was created successfully

        Parameters:
            name (str): Name for the new organization
            user (str): User for grafana (typically admin)
            password (str): Password for the grafana user
            host (str): Host for the grafana server
            port (int): Port for the grafana server
        Returns:
            orgid (int): Id of the organization created or found
            None: If there was an issue creating the org
    '''

    json_data = {
        'name': f'{name}',
    }

    access = f'http://{user}:{password}@{host}:{port}'
    url = access + '/api/orgs'
    
    response = requests.post(url, json=json_data)

    data = json.loads(str(response.content, 'utf-8'))
    
    if data['message'] == 'Organization name taken':
        url = access + '/api/orgs'

        response = requests.get(url)

        data = json.loads(str(response.content, 'utf-8'))

        for org in data:
            if org['name'] == f'{name}':
                return int(org['id'])
        return None

    if data['message'] == 'Organization created':
        return int(data['orgId'])

    if data['message'] == 'invalid username or password':
        raise InvalidUsernameOrPasswordError(data['message'])


def switch_org(org_id:int, user:str, password:str, host:str, port:int) -> None:
    """
    Returns none if successful in switching provided user to organization

        Parameters:
            org_id (str): Id for the organization
            user (str): User for grafana (typically admin)
            password (str): Password for the grafana user
            host (str): Host for the grafana server
            port (int): Port for the grafana server
    """

    access = f'http://{user}:{password}@{host}:{port}'
    url = access + '/api/user/using/' + str(org_id)
    
    response = requests.post(url)

    data = json.loads(str(response.content, 'utf-8'))

    if (not "message" in data or 
        not data['message'] == 'Active organization changed'):

        raise OrganizationError('Message response missing!')


def main(args):
    GRAFANA_NAME = 'trusted'
    GRAFANA_USER = 'admin'
    GRAFANA_PASS = 'admin'
    GRFANA_HOST = 'localhost'
    GRAFANA_PORT = 3000
    API_KEY_FILE = None

    while args:
        current_argument = args[0]
        if current_argument in ('-h', '--help'):
            print('help_()')
            exit(0)
        if current_argument in ('-H', '--host'):
            GRFANA_HOST = args[1]
        if current_argument in ('-P', '--port'):
            GRAFANA_PORT = args[1]
        if current_argument in ('-u', '--user'):
            GRAFANA_USER = args[1]
        if current_argument in ('-p', '--pass'):
            GRAFANA_PASS = args[1]
        if current_argument in ('-n', '--name'):
            GRAFANA_NAME = args[1]
        if current_argument in ('-f', '--file'):
            API_KEY_FILE = Path(args[1])
        del args[0]

    try: 
        check_arguments(GRAFANA_NAME, GRAFANA_USER, GRAFANA_PASS, GRFANA_HOST, 
                        GRAFANA_PORT, API_KEY_FILE)
    except MissingArgumentError as error:
        raise SystemExit(error)

    api_exists = check_api_key_file(GRAFANA_NAME, API_KEY_FILE)

    if api_exists:
        status = {
            'success': True,
            'message': 'API key already exists',
        }
        return status

    try:
        org_id = post_org(GRAFANA_NAME, GRAFANA_USER, GRAFANA_PASS, 
                          GRFANA_HOST, GRAFANA_PORT)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)            
    except InvalidUsernameOrPasswordError as error:
        raise SystemExit(error)

    try:
        switch_org(org_id, GRAFANA_USER, GRAFANA_PASS, GRFANA_HOST,
                   GRAFANA_PORT)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)
    except OrganizationError as error:
        raise SystemExit(error)
    
    try:
        api_key = create_api_token(GRAFANA_NAME, GRAFANA_USER, GRAFANA_PASS,
                                   GRFANA_HOST, GRAFANA_PORT)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)
    except CreateAPITokenError as error:
        raise SystemExit(error)

    with API_KEY_FILE.open('w') as file:
        json.dump(api_key, file, sort_keys=True, indent=4)

    api_exists = check_api_key_file(GRAFANA_NAME, API_KEY_FILE)

    if api_exists:
        status = {
            'success': True,
            'message': 'API key created',
        }
        return status
    else:
        status = {
            'success': False,
            'message': 'API failed to create',
        }
        return status


if __name__ == "__main__":
    status = main(argv[1:])
    print(status['message'])
    if status['success']:
        exit(0)
    else:
        exit(1)
