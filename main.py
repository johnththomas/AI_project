import openai # pip install openai
from dotenv import load_dotenv
import os
import json
import getch

from termcolor import colored
from os import system as x
from menu import VerticalMenu
from chat import BusinessIdeasChat
from create_report import create_report_as_md_file, md_to_pdf,send_email



def create_prompt():  #User input
    skills_comp=input("What are your primary skills and competencies?: ")
    experience=input("In which industries or sectors do you have experience or education?: ")
    hobbies=input("What hobbies or interests do you have?: ")
    assets=input("What assets or resources are available to you? (e.g., equipment, space, starting capital, etc.): ")
    business_format=input("What business format do you prefer? (e.g., online, offline, franchise, startup, etc.): ")
    markets=input("Are there specific markets or audiences you would like to target?: ")
    level_risk=input("What level of risk are you willing to take? (e.g., high, medium, low): ")
    plans=input("What is your long-term plan or vision for the business?: ")
    country=input("Which country do you plan to operate in?: ")

    prompt=(
        """Considering the importance of individual skills, interests, and assets for 
        successful business, how can these elements be best utilized for idea generation?

        My primary skills and competencies: 
        """
        +skills_comp
        +"\nI have experience and/or education in: "
        +experience
        +"\nMy hobbies are: "
        +hobbies
        +"\nI have access to: "
        +assets
        +"\nMy business format preference: "
        +business_format
        +"\nI would specifically like to target these markets:"
        +markets
        +f"\nI am willing to take {level_risk} level of risk,"
        +"My vision for my business in the long term: "
        +plans
        +f"\nI plan to operate in {country}."
        +"\nGive me please three best business ideas."
    )

    return prompt

class ChatInMenu(BusinessIdeasChat,VerticalMenu):
    def __init__(self, initial_prompt):
        print("\n"+colored("Generating 3 business ideas for you...","blue"))
        super().__init__(initial_prompt)  #initializing chat, also creating the seeding list_of menu_items for the menu
        self.menu_title=colored("IdeaAlchemy: Craft Your Success","light_yellow",attrs=["bold"])+"\n\nUse "+colored("a s w", "red")+" navigate, "+colored("f","green")+" to select or unselect, "+colored("d","blue")+" to open or to execute, "+colored("x","red")+" to create report and exit."
        self._list_of_menu_items[0]=self.menu_title
        VerticalMenu.__init__(self,self._list_of_menu_items,25) #25 is a universal constant :) Ugly, I know

    def execute(self, *args):
        """Elaborates on all selected items one by one and prints the response. A conversation history is emulated for each prompt to save tokens and in order not to confuse the AI too much"""

        x("clear")
        for i in self.selected:
            x_coords=self.coords[:-1]
            x_coords.append(i)
            print(colored(f"Elaborating on {self._access_menu_item(x_coords)[0]}...","blue"))
            self.list_of_menu_items=self.create_prompt(x_coords)
            for item in self._access_database(x_coords)[1:]:
                print(item["num"]+". "+colored(item["title"],"green")+"\n"+item["content"])
        print("\nPress any key to return to menu or "+colored('x','red')+" to stop and generate report")
        mov=getch.getch()
        self.selected.clear()
        return mov  #if mov==x it will actually trigger break in navigate_menu()!
    
    def navigate_menu(self):
        super().navigate_menu()
        """After normal menu work is done and exit is done regularly with 'x' key, log, report and email are generated. Meaning that if you decide to stop the code with ctrl-C all data is lost. Maybe should (have) fix(ed) that..."""

        data=self._access_database([])
        with open("log.json", "w") as file:
            json.dump(data,file, indent=4)
        create_report_as_md_file(data,"report.md")
        with open("report.md", "r") as file:
            md_content = file.read()
            md_to_pdf(md_content, "report.pdf")
        print("Do you want this report sent to your e-mail(y/n)?")
        while True:
            ans=getch.getch()
            if ans.lower()=="y":
                to_email = input('Enter your valid email id: ')
                send_email("Your businessPDF is attached", to_email, "report.pdf")
                break
            if ans.lower()=="n":
                break
def main():
    # Set your OpenAI API key
    #openai.api_key = ""

    load_dotenv()
    openai.api_key=os.getenv('API_KEY')
    
    
    x("clear")
    prompt=create_prompt()
   


    b=ChatInMenu(prompt)#upon initialization the initial_prompt is sent to Chatgpt, list_of_menu_items is created, menu is initialized with the latter and printed. Below AI response is printed.
    for item in b._access_database([])[1:]:
        print(item["num"]+". "+colored(item["title"],"green")+"\n"+item["content"])
    print("\n")
    print(colored("Navigate the menu to choose what ideas to elaborate on. Press any key to get to menu.","blue"))
    getch.getch()
    
    b.navigate_menu()
    

if __name__ == "__main__":
    main()