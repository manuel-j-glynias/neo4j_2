import sys

import requests
from neo4j import GraphDatabase
import typing
import datetime

def send_mutation(mutation_payload:str, server:str) -> str:
    url = "http://" + server + ":7474/graphql/"
    headers = {
      'Authorization': 'Basic bmVvNGo6b21uaQ==',
      'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data = mutation_payload)
    if not response.ok:
        response.raise_for_status()
        sys.exit()

    responseBody: str = response.json()

    return responseBody

# createEditableStatement(
# deleted: Boolean!
# edit_date: String!
# editor: String!
# field: String!
# id: ID!
# statement: String!): String

def createEditableStatement(statement:str, field:str, editor:str, esList:list) -> (str,str):
    now = datetime.datetime.now()
    edit_date:str = now.strftime("%Y-%m-%d-%H-%M-%S-%f")
    numES: int = len(esList)
    id:str = 'es_' + str(numES)
    esList.append(id)
    s = f'''{id} : createEditableStatement(deleted: false, edit_date: \\"{edit_date}\\", editor: \\"{editor}\\",field: \\"{field}\\", id: \\"{id}\\",statement: \\"{statement}\\"),'''
    return s, id

# addCompoundStatementFact1(fact1: [ID!]!id: ID!): String
# Adds Fact1 to CompoundStatement entity
#
# addCompoundStatementFact2(fact2: [ID!]!id: ID!): String
# Adds Fact2 to CompoundStatement entity
#
# createCompoundStatement(id: ID!name: String!): String

def create_compund_statement(statement1:str, statement2:str, cs_name:str, editor:str, csList:list, esList:list) -> str:
    s = ''
    numCS: int = len(csList)
    id: str = 'cs_' + str(numCS)
    s += f'''{id}: createCompoundStatement(id: \\"{id}\\", name: \\"{cs_name}\\"),'''
    csList.append(id)
    field1: str = 'fact1_' + id
    field2: str = 'fact2_' + id
    (m, id1) = createEditableStatement(statement1,field1,editor,esList)
    s += m
    s += f'''addCompoundStatementFact1(fact1:[\\"{id1}\\"], id:\\"{id}\\"),'''
    (m, id2) = createEditableStatement(statement2, field2, editor, esList)
    s += m
    s += f'''addCompoundStatementFact2(fact2:[\\"{id2}\\"], id:\\"{id}\\"),'''
    return s



def write_initial_mutation(csList:list, esList:list, server:str):
    s: str = '{"query":"mutation {'
    s += create_compund_statement("statement1 v.1", "statement2 v.1", 'compound1', 'mglynias', csList, esList)
    s += '}"}'
    print(s)
    responseBody = send_mutation(s, server)
    print(responseBody)


def write_new_fact1(old_id:str, statement:str,csList:list, esList:list, server:str):
    s: str = '{"query":"mutation {'
    id = csList[0]
    field:str = 'fact1_' + id
    s += f'''deleteCompoundStatementFact1(fact1:[\\"{old_id}\\"], id:\\"{id}\\"),'''
    (m, id1) = createEditableStatement(statement, field, 'mglynias', esList)
    s += m
    s += f'''addCompoundStatementFact1(fact1:[\\"{id1}\\"], id:\\"{id}\\"),'''
    s += '}"}'
    print(s)
    responseBody = send_mutation(s, server)
    print(responseBody)


def write_mutation(server:str) -> None:
    csList: list = []
    esList: list = []
    write_initial_mutation(csList, esList, server)
    write_new_fact1('es_0','statement1 v.2',csList,esList,server)
    write_new_fact1('es_2','statement1 v.3',csList,esList,server)
    write_new_fact1('es_3','statement1 v.4',csList,esList,server)



def main():
    server:str = 'localhost'
    # server: str = '165.227.89.140'
    uri = "bolt://" + server + ":7687"

    with open('schema.graphql', 'r') as file:
        idl_as_string = file.read()

    driver = GraphDatabase.driver(uri, auth=("neo4j", "omni"))
    with driver.session() as session:
        tx = session.begin_transaction()
        tx.run("match(a) detach delete(a)")
        result = tx.run("call graphql.idl('" + idl_as_string + "')")
        print(result.single()[0])
        tx.commit()
    driver.close()
    write_mutation(server)




if __name__ == "__main__":
    main()

