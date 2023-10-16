import requests
import base64
from datetime import datetime
import csv


def auth():
    # Abra o arquivo para leitura
    with open('auth.txt', 'r') as arquivo:
        # Leia e armazene cada linha em uma variável
        organization = arquivo.readline().strip()
        project = arquivo.readline().strip()
        personal_access_token = arquivo.readline().strip()
        query_id = arquivo.readline().strip()

    # Codificar o token de acesso pessoal para a autenticação
    token = base64.b64encode(bytes(f":{personal_access_token}", "utf-8")).decode("utf-8")

    # Definir cabeçalhos para a solicitação
    headers = {
        "Authorization": f"Basic {token}"
    }
    return organization, project, query_id, headers


def get_query_results(organization, project, query_id, headers):
    task_ids = []
    # URL da API para extrair uma consulta específica
    # fonte: https://learn.microsoft.com/pt-br/rest/api/azure/devops/wit/wiql/query-by-wiql?view=azure-devops-rest-7.0&tabs=HTTP
    url = f'https://dev.azure.com/{organization}/{project}/_apis/wit/wiql/{query_id}?api-version=7.1-preview.2'

    # Fazer a solicitação GET
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        query_data = response.json()
        for query in query_data["workItems"]:
            task_ids.append(query['id'])
    else:
        print("Falha ao buscar a consulta. Código de status:", response.status_code)
    return task_ids


def get_items_results(task_ids, organization, headers):
    # Lista para armazenar os estados das atualizações
    states = []
    for item in task_ids:
        #  fonte: https://learn.microsoft.com/pt-br/rest/api/azure/devops/wit/work-items/list?tabs=HTTP
        url_task = f'https://dev.azure.com/{organization}/{project}/_apis/wit/workItems/{item}/updates?api-version=7.0'
        response = requests.get(url_task, headers=headers)
        if response.status_code == 200:
            task_data = response.json()
            # print(json.dumps(task_data, indent=4))
            updates = task_data['value']

            for update in updates:
                try:
                    # state = update['revisedDate']
                    work_id = update['workItemId']
                    work_type = updates[0]['fields']['System.WorkItemType']['newValue']
                    squad = updates[0]['fields']['System.NodeName']['newValue']
                    old_state = update['fields']['System.State']['oldValue']
                    new_state = update['fields']['System.State']['newValue']
                    old_date = update['fields']['Microsoft.VSTS.Common.StateChangeDate']['oldValue']
                    new_date = update['fields']['Microsoft.VSTS.Common.StateChangeDate']['newValue']
                    start_date = datetime.strptime(old_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                    end_date = datetime.strptime(new_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                    total_days = round(((end_date - start_date).total_seconds()) / 3600 / 24, 2)
                    hours_btw_dates = round(((end_date - start_date).total_seconds()) / 3600, 2)
                    states.append([work_id,
                                   work_type,
                                   squad,
                                   old_state,
                                   old_date,
                                   new_state,
                                   new_date,
                                   total_days,
                                   hours_btw_dates
                                   ])
                except:
                    continue

            # Agora, imprima todos os estados coletados
            for state in states:
                print(state)
        else:
            print(f"A solicitação falhou com o código de status: {response.status_code}")
    return states


def salvar_csv(states):
    with open('results.csv', "w", newline="", encoding="utf-8") as arquivo_csv:
        escritor_csv = csv.writer(arquivo_csv, delimiter=";")
        # Escrever o cabeçalho
        cabecalho = ['id',
                     'type',
                     'squad',
                     'old_state',
                     'old_date',
                     'new_state',
                     'new_date',
                     'total_days',
                     'hours_btw_dates'
                     ]
        escritor_csv.writerow(cabecalho)
        for linha in processed_data:
            escritor_csv.writerow(linha)


organization, project, query_id, headers = auth()
task_ids = get_query_results(organization, project, query_id, headers)
processed_data = get_items_results(task_ids, organization, headers)
salvar_csv(processed_data)
