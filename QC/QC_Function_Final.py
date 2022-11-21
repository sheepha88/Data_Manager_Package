import pandas as pd


## 컬럼명 비교

def columns_QC(columns1 , columns2):
    for i in range(len(columns1)):
        if columns1[i]!=columns2[i]:
            print(columns1[i] ,",", columns2[i])
            
            
            
            
## value값 비교
#dataframe1.equals(dataframe2)

def values_QC(dataframe1 , dataframe2):
    for i in range(len(dataframe1)):
        for z in range(len(dataframe1.columns)):
            if not pd.Series(dataframe1.iloc[i,z]).equals(pd.Series(dataframe2.iloc[i,z])):
                # print(dataframe1.iloc[i,z] ,dataframe2.iloc[i,z] )
                print("Y",dataframe1.loc[i , ["USUBJID" , "VISIT" , "READER" , dataframe1.columns[z]]] )
                print("")
                print("L" , dataframe2.loc[i , ["USUBJID" , "VISIT" , "READER" , dataframe2.columns[z]]] )
                print("")