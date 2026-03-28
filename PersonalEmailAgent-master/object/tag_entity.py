from pydantic import BaseModel

class Tag(BaseModel):
    name:str="tag_name"
    value:str="tag_value"
    
    
if __name__=="__main__":
    t=Tag(name="color",val="red")
    print(t)