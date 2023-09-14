#from os import system as x
import os
#from termcolor import colored
import openai # pip install openai
from dotenv import load_dotenv
import re
#import getch
import json

class BusinessIdeasChat:
    def __init__(self,initial_prompt):
        load_dotenv()
        openai.api_key=os.getenv('API_KEY')
        self.initial_prompt=initial_prompt
        self.__expert="business consultant"
        self.menu_title="Menu"
        self._list_of_menu_items=[self.menu_title]
        self._make_system_role()
        self.__initialize_conversation()
        """Get and analyze first Chatgpt answer to <initial_prompt>"""
        self.response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.conversation
            )
        self.assistant_message=self.response['choices'][0]['message']['content']
        self.__database=self._parse_response()
        """
        The database has nested format. Each level has the form:
        [<AI answer at this level>, 
        {"num": <number>, 
        "title": <short description of the item>,
        "expert": <suggested expert for the item>,
        "content": <part of AI answer referring to the item>,
        "prompt": <user prompt to elaborate on the item. Present only if the user asked to elaborate>,
        "elaborate": [<nested list of the same format>]}] Present only if the user asked to elaborate
        """
        for i in self.__database[1:]:  #List of menu items is initialised with "title"'s from the database. It will be used to initialize menu
            self._list_of_menu_items.append([i["title"]])
        

    def _make_system_role(self): #changes the system role according to the suggested expert for the particular prompt
        self.system_role=f"""Imagine it's September 2021.You are the best {self.__expert} in the world with 25 years of experience and in depth knowledge of business, markets, strategies, start-ups etc. No need to mention the current year in the answer. All answers are to be given strictly in form of numbered lists of items with a new line after each item including the final one. Each list item is given strictly in the format: number. #short description in maximum five word# $the expert to be addressed for elaboration of this item$ - |longer description of the item in imperative form for the second person| Use only these seperators:#$| Use those separators only in the beginning and the end of the logical group. Do not write an introduction or a conclusion
        """

    def __initialize_conversation(self):#initializes initial prompt. Also used every time for emulating the conversation with AI in <create_prompt>
        self.conversation=[{"role": "system", "content": self.system_role},{"role": "user", "content": self.initial_prompt}]

    def _parse_response(self): # parses the response and returns the next level entry to the database
        recog_pattern = "(\d+)\.\s*#([^#]+)#\s*\$([^$]+)\$[\s-]*\|(.+)[\|\n]"
        matches = re.findall(recog_pattern,self.assistant_message+"\n")
        database_entry=[self.assistant_message]
        for match in matches:
            database_entry.append(
                {
            "num" : match[0],
            "title" : match[1].strip(),
            "expert" : match[2].strip(),
            "content" : match[3].strip(" |")
                }
            )
        return database_entry
        
    def create_prompt(self,coords):
        cur_dialog_step=self.__database
        self.__initialize_conversation()
        for i in coords[:-1]: #emulates the dialogue as if user was choosing elements of coords consequently
            self.conversation.append({"role": "assistant", "content": cur_dialog_step[0]})
            cur_dialog_step=cur_dialog_step[i]
            self.conversation.append({"role": "user", "content": cur_dialog_step["prompt"]})
            cur_dialog_step=cur_dialog_step["elaborate"]
        self.conversation.append({"role": "assistant", "content": cur_dialog_step[0]})
        cur_dialog_step=cur_dialog_step[coords[-1]]
        self.__expert=cur_dialog_step["expert"]
        self._make_system_role() #new system role with new expert
        self.conversation[0]["content"]=self.system_role
        if len(coords)==1: #if asked to elaborate on business proposal
            prompt=f"You are the best {self.__expert} in the whole world, with 25 years experience. I am your client and i want to start {cur_dialog_step['title']}. Describe in detail and write what is needed to start. No need to mention the current year in the answer. Write strictly in the format: number. #name of the business action# $expert to address for detailed information$ - |description of the business action as a single block in imperative form for the second person| Use only these seperators:#$| Use those separators only in the beginning and the end of the logical group. Do not write an introduction or a conclusion"
        else:  #if asked to elaborate on a deeper level
            prompt=f"Your current choice of business action is {cur_dialog_step['title']}. Imagine it's September 2021. you're the best {self.__expert} in the whole world, with 25 years of experience. I'm your client and i want you to fetch me a detailed report on bullet points to this business action using the following information: \n{cur_dialog_step['content']} \nNo need to mention the current year in the answer. Write strictly in the format: number. #name of the bullet point# $expert to adress for more detailed information about the bullet point$ - |description of the bullet point as a single block in imperative form for the second person| Use only these seperators:#$| Use those separators only in the beginning and the end of the logical group. Do not write an introduction or a conclusion"
        
        self.conversation.append({"role": "user", "content": prompt})
        self.response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.conversation
            )
        self.assistant_message=self.response['choices'][0]['message']['content']
        self.__append_database(coords,prompt,self._parse_response()) # adds prompt and response to the database
        self.__append_list_menu_items(coords)
        return self._list_of_menu_items #used to update the menu structure

    def __append_list_menu_items(self,coords):
        """Adds 'title's from database to the nested list_of_menu_items according to list <coords>"""

        def append_list_menu_items(lst,data,coords):
            if len(coords)==1:
                lst[coords[0]].extend([i["title"]] for i in data[coords[0]]["elaborate"][1:])
            else:
                append_list_menu_items(lst[coords[0]],data[coords[0]]["elaborate"],coords[1:])
            return lst
        
        #data=self.__database
        lst=self._list_of_menu_items
        self._list_of_menu_items=append_list_menu_items(lst,self.__database,coords)

        

    def __append_database(self, coords, prompt, elaborate):
        """Adds 'prompt's and "elaborate" lists to database to a location given by the list <coords>"""
        
        def append_database(data, coords, prompt, elaborate):
            if len(coords)==1:
                data[coords[0]]["prompt"]=prompt
                data[coords[0]]["elaborate"]=elaborate
            else:
                append_database(data[coords[0]]["elaborate"],coords[1:],prompt,elaborate)
            return data
        
        data=self.__database
        self.__database=append_database(data, coords, prompt, elaborate)

    def _access_database(self,coords):
        """Accesses the database at the location given by <coords> If coords==[] it can be used to read the private __database"""

        data=self.__database
        for i in coords:
            data=data[i]["elaborate"]
        return data

    
        
            


if __name__ == "__main__":
    init_prompt='Considering the importance of individual skills, interests, and assets for successful business, how can these elements be best utilized for a business idea generation? My primary skills and competencies: perseverence.I have experience and/or education in: business. My hobbies are: cooking. I have access to: car, internet. My business format preference: online.I would specifically like to target these markets:Germany. I am willing to take low level of risk,My vision for my business in the long term: Own a profitable business. Give me three best business ideas. Write strictly in the format: number. #name of the idea# $the area expert$ - |business idea as a single block in imperative form for the second person| Use only these seperators:#$| do not write an introduction or a conclusion'
    b=BusinessIdeasChat(init_prompt)
    #print(b._BusinessIdeasChat__database)
    print(b.create_prompt([2]))
    #print(b._BusinessIdeasChat__database)
    print(b.create_prompt([2,2]))
    #print(b._BusinessIdeasChat__database)
    print(b.create_prompt([2,2,1]))
    #print(b._BusinessIdeasChat__database)
    print(b.create_prompt([1]))
    #print(b._BusinessIdeasChat__database)
    print(b.create_prompt([1,2]))

    with open("log.json", "w") as file:
        json.dump(b._BusinessIdeasChat__database,file, indent=4)


    
