import requests
import sys
import os
from time import sleep
from datetime import datetime
import pandas as pd
from pathlib import Path


class QueryRunner:
    TOKEN = "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"
    NUMBER_OF_ATTEMPTS = 15
    NUMBER_ITERATION = 10
    GITHUB_API_ENDPOINT = "https://api.github.com/graphql"

    graphQLDuration = []
    graphQLSize = []
    restDuration = []
    restSize = []
    hasFilter = []
  
    def __init__(self):
        super(QueryRunner, self).__init__()

    def run_graphql_query(self, query, attemp, token):

        headers = {"Authorization": "Bearer " + token}

        request = requests.post(self.GITHUB_API_ENDPOINT, headers=headers, json={"query": query})

        if request.status_code == 200:
            return request.json()
        elif attemp <= self.NUMBER_OF_ATTEMPTS:
            print("Tentativa de conexão falhou :(. {}/{} Tentando novamente...".format(attemp,
                  self.NUMBER_OF_ATTEMPTS))
            sleep(1)
            return self.run_graphql_query(query, attemp + 1, token)
        else:
            raise Exception("Tentativa de conexão falhou com o erro: {}. {}".format(
                request.status_code, query))
    
    def run_rest_request(self, url, attemp, token):

        headers = {'Authorization': 'token ' + token, 'Content-Type': 'application/json; charset=utf-8'}
        
        request = requests.get(url=url, headers=headers)

        if request.status_code == 200:
            return request.json()
        elif attemp <= self.NUMBER_OF_ATTEMPTS:
            print("Tentativa de conexão falhou :(. {}/{} Tentando novamente...".format(attemp,
                  self.NUMBER_OF_ATTEMPTS))
            sleep(1)
            return self.run_rest_request(url, attemp + 1, token)
        else:
            raise Exception("Tentativa de conexão falhou com o erro: {}.".format(
                request.status_code))


    def save_results_to_csv(self):
        csv_file_name = "results.csv"
        data_to_file = []

        if not os.path.isfile(csv_file_name):
            results = pd.DataFrame()
        else:
            csv_path = Path('./'+csv_file_name)
            results = pd.read_csv(csv_path, header=0, sep=';')

        for i in range(len(self.graphQLDuration)):
            row = {
                "GraphQL Duration": self.graphQLDuration[i],
                "GraphQL Size (bytes)": self.graphQLSize[i],
                "REST Duration": self.restDuration[i],
                "REST Size (bytes)": self.restSize[i],
                "Has Filter": self.hasFilter[i]
            }
            data_to_file.append(row)

        results = pd.concat([results, pd.DataFrame.from_records(data_to_file)])

        results.to_csv(csv_file_name, index=False, sep=';')

    def create_query_graphql(self, filter=False):

        if not filter:
            query = """
                query github {
                    search(query: "stars:>100", type:REPOSITORY, first:10) {
                        nodes {
                            ... on Repository {
                                id
                                name
                                nameWithOwner
                                url
                                createdAt
                                isPrivate
                                stargazers { totalCount }
                                }
                            }
                        pageInfo {
                                hasNextPage
                                endCursor
                        }
                    }
                }
            """ 

        else:
            query = """
            query github {
                query github {
                    search(query: "stars:>100 language:java", type:REPOSITORY, first:10) {
                        nodes {
                            ... on Repository {
                                id
                                name
                                nameWithOwner
                                url
                                createdAt
                                isPrivate
                                stargazers { totalCount }
                                }
                            }
                        pageInfo {
                                hasNextPage
                                endCursor
                        }
                    }
                }
            """
        return query

    def fetch_graphql_data(self,filter):
    
        query = self.create_query_graphql(filter)

        response = self.run_graphql_query(query, 1, self.TOKEN)
        graphql_request_size = sys.getsizeof(response)
        self.graphQLSize.append(graphql_request_size)
    
    def fetch_rest_data(self,filter):

        if not filter:
            url = 'https://api.github.com/search/repositories?q=stars:>100&per_page=10'
        else: 
            url = 'https://api.github.com/search/repositories?q=language:java+stars:>100&per_page=10'
        
        response = self.run_rest_request(url, 1, self.TOKEN)
        rest_request_size = sys.getsizeof(response)
        self.restSize.append(rest_request_size)
       
    # Função principal da classe
    def main(self):	

        for filter in [False, True]:
            iteration = 1
            while iteration <= self.NUMBER_ITERATION:
                
                print("GraphQL")

                start_time = datetime.now()
                self.fetch_graphql_data(filter)
                end_time = datetime.now()

                duration = (end_time - start_time).total_seconds() * 1000

                self.graphQLDuration.append(duration)

                print("REST")

                start_time = datetime.now()
                self.fetch_rest_data(filter)
                end_time = datetime.now()

                duration = (end_time - start_time).total_seconds() * 1000

                self.restDuration.append(duration)
                self.hasFilter.append(filter)

                print(f"Iteration: {iteration}")

                iteration += 1
               
        self.save_results_to_csv()
        
# Obter resultados do QueryRunner
qr = QueryRunner()
qr.main()