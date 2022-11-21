import numpy as np
import pandas as pd
import datetime
import warnings
import openpyxl
warnings.filterwarnings("ignore")



#----------------------------------------------------------------
# Indicator( TRGIND , NTRGIND ) 가 No 일 경우, Rseponse( TRGRESP , NTRGRESP) 는 "NE" (Baseline 제외)
# 
def indicator_NE(dataframe , visitname , col_indicator , value , col_response , result):
    
    new_dataframe = dataframe.copy(deep = True)
    
    for i in range(len(new_dataframe)):
        if new_dataframe.loc[i,"VISIT"]!= visitname:
        
            if new_dataframe.loc[i,col_indicator]== value:
                new_dataframe.loc[i,col_response]= result
            
    return new_dataframe
            
# indicator_NE(df , "Bseline", "TRGIND" , "No", "TRGRESP" , "NE")


#----------------------------------------------------------------
# Indicator( TRGIND , NTRGIND , New Lesion ) 가 No 일 경우, Response 이전 컬럼들은 모두 np.nan
# 
#col_indicator : TRGIND
#value : No
#col_range1 : TRGOC_1 (TRGIND 이후의 값)
#col_range2 : TRASCAH_DATE (Response이전의 값)
def indicator_NAN(dataframe , col_indicator , value , col_range1 , col_range2 , result):
    
    new_dataframe = dataframe.copy(deep = True)
    
    for i in range(len(new_dataframe)):
        if new_dataframe.loc[i,col_indicator]== value:
            new_dataframe.loc[i,col_range1:col_range2]= result
            
    return new_dataframe
            
# indicator_NAN(df , "TRGIND" , "No", "TRGOC_1", "TRASCAH_DATE" , np.nan)