from fastapi import FastAPI, HTTPException
from enum import Enum
from pydantic import BaseModel
from typing import Union

import pandas as pd
import numpy as np

import sklearn

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import FunctionTransformer
from sklearn.pipeline import Pipeline

import pickle



app = FastAPI()


sample_test = {
    'total_meters':[58.2, 60.0],
    'kitchen_meters':[21.0, 12.0],
    'dist_to_subway, min':[15.0, 25.0],
    'admin_okrug':['СВАО', 'СВАО'],
    'subway':['Ботанический сад', 'ВДНХ'],
    'is_skyscraper': ['False', 'False'],
    'class_real':['комфорт', ''],
    'way_to_subway':['пешком', 'пешком'],
    'wc_type':['совмещенный', 'раздельный'],
    'house_type':['Монолитный', 'кирпичный'],
    'flat_type':['Новостройка', 'Вторичка'],
    'rooms': [2, 2],
    'year_of_construction':[2021, 1995],
    'wc_count':[2, 1],
    'district':['р-н Останкинский', 'р-н Алексеевский'],
    'floor_type':['usual', 'usual']
}


class Flat(BaseModel):
    total_sq: float
    kitchen_sq: float
    rooms: int
    okrug: str
    district: str = ''
    subway: str
    year_of_construction: int = 2000
    flat_type: FlatType = FlatType.new
    to_subway: WayToSubway = WayToSubway.foot
    dist_to_subway : float = 15.0
    wc_count: int = 1
    is_skyscraper: bool = False
    flat_class : FlatClass = FlatClass.comfort
    wc_type : WcType = WcType.combined
    house_type : HouseType = HouseType.panel


class FlatType(str, Enum):
    new = 'Новостройка'
    second = 'Вторичка'

class HouseType(str, Enum):
    mono = 'Монолитный'
    panel = 'Панельный'
    
class FlatClass(str, Enum):
    low = 'эконом'
    comfort = 'комформ'
    business = 'бизнес'
    premium = 'премиум'
    elite = 'элитный'
    
class WayToSubway(str, Enum):
    foot = 'пешком'
    second = 'на транспорте'

class WcType(str, Enum):
    combined = 'совмещенный'
    separated = 'раздельный'


flats = {}


@app.get('/')
async def root():
    return {}

@app.post("/post")
def get_post() -> Timestamp:
    #global dog_counter
    time = Timestamp(id=0, timestamp=0)
    #dogs[dog_counter] = Dog(name='', pk=dog_counter, kind=DogType.terrier)
    #dog_counter += 1
    return time

@app.post('/dog')
async def create_dog(dog: Dog) -> Dog:
    if dog.pk in dogs:
        raise HTTPException(
            status_code=422, detail=f"Dog with {dog.pk=} already exists."
        )
    else:
        global dog_counter
        if dog.pk is None:
            dog.pk = dog_counter
        dogs[dog_counter] = dog
        dog_counter += 1
        return dog


@app.get('/dog')
async def get_dogs(kind: DogType = None) -> list[Dog]:
    def check_dog(dog: Dog):
        return kind is None or dog.kind is kind

    selection = [val for key, val in dogs.items() if check_dog(val)]
    return selection


@app.get('/dog/{pk}')
async def get_dog_by_pk(pk: int) -> Dog:
    if pk not in dogs:
        raise HTTPException(
            status_code=404, detail=f"Dog with {pk=} does not exist."
        )
    return dogs[pk]


@app.patch('/dog/{pk}')
async def update_dog(pk: int, dog: Dog) -> Dog:
    if pk not in dogs:
        raise HTTPException(status_code=404, detail=f"Dog with {pk=} does not exist.")
    if all(info is None for info in (dog.name, dog.kind)):
        raise HTTPException(status_code=404, detail="You need to provide name and kind for an update")

    update_dog = dogs[pk]
    if dog.name is not None:
        update_dog.name = dog.name
    if dog.kind is not None:
        update_dog.kind = dog.kind
    return update_dog