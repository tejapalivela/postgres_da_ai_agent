import os
from postgres_da_ai_agent.modules.db import PostgresManager
from postgres_da_ai_agent.modules import llm    

import dotenv
import argparse

dotenv.load_dotenv()

assert os.environ.get('DATABASE_URL'), "url not found"
assert os.environ.get('OPENAI_API_KEY'), "api key not found"

DB_URL = os.environ.get('DATABASE_URL')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

POSTGRES_TABLE_DEFINITIONS_CAP_REF="TABLE_DEFINITIONS"
RESPONSE_FORMAT_CAP_REF = "RESPONSE_FORMAT"


SQL_DELIMITER = "---------"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="The prompt for the AI") 
    args = parser.parse_args()

    if not  args.prompt:
        print("Please provide a prompt")
        return
    
    with PostgresManager() as db:
        print("prompt v1", args.prompt)  

        db.connect_with_url(DB_URL)
    
        table_definitions = db.get_table_definitions_for_prompt()

        prompt = llm.add_cap_ref(
            args.prompt, 
            f"Use these {POSTGRES_TABLE_DEFINITIONS_CAP_REF} to satisfy the database query.", 
            POSTGRES_TABLE_DEFINITIONS_CAP_REF, 
            table_definitions,
            )
        
        print("prompt v2", prompt)  

        prompt = llm.add_cap_ref(
            prompt, 
            f"\n\nI want to directly extract the sql query from your response. Follow the instructions strictly, Respond exactly in this format {RESPONSE_FORMAT_CAP_REF} where you should replace the question in the <> with the value.",
            RESPONSE_FORMAT_CAP_REF,
            f"""<explanation of the sql query>
            < replace the <> with only sql query no other instructions after the following delimiters ------- >
{SQL_DELIMITER}
< >""")
        
        print("prompt v3", prompt)  

        prompt_response = llm.prompt(prompt)

        print("prompt_response", prompt_response)


        sql_query = prompt_response.split(SQL_DELIMITER)[1].strip()

        print("sql_query------>", sql_query)   
        result = db.run_sql(sql_query)
        print("result", result)

    pass

if __name__ == '__main__':
    main()