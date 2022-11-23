import numpy as np
import pandas as pd
import datetime
import warnings
import openpyxl
warnings.filterwarnings("ignore")


# MMF에서 조정자가 Pick한 Analyst 표시하고 싶을 때 사용
# 
def ADJ_PICK_Flag(dataframe, USUBJID , Baselinename , ADJUDICATOR , Analyst_1 , Analyst_2 , Flag_col , columns):
    
    # 해당 대상자의 baseline만 뽑아낸 테이블
    baseline_Dataframe = dataframe[ (dataframe["USUBJID"]==USUBJID) & (dataframe["VISIT"]==Baselinename)].reset_index(drop=True)
    
    # #해당 대상자의 전체 visit 뽑아낸 테이블
    # visit_Dataframe = dataframe[ (dataframe["USUBJID"]==USUBJID)].reset_index(drop=True)
    
    # 조정자의 컬럼에 해당하는 series값
    ADJ_series = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==ADJUDICATOR].index)[0] , columns]
    # Anaslyst#1의 컬럼에 해당하는 series값
    Analyst_1_series = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_1].index)[0] , columns]
    # Anaslyst#2의 컬럼에 해당하는 series값
    Analyst_2_series = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_2].index)[0] , columns]


    # 만약 조정자의 컬럼에 해당하는 series값이 모두 nan이라면(조정자가 아직 판독하지 않은 경우라면) 제외해라
    if not all([pd.isnull(x) for x in ADJ_series.values.tolist()]):


        # 조정자의 columns값과 Analyst#1의 columns값이 baseline에서 같다면 analyst#1을 선언
        if ADJ_series.equals(Analyst_1_series):
                ADJ_Pick_Analayst = Analyst_1
                
        # 조정자의 columns값과 Analyst#1의 columns값이 baseline에서 같다면 analyst#2을 선언
        elif ADJ_series.equals( Analyst_2_series):
                ADJ_Pick_Analayst = Analyst_2
        
        
        # 헤당 대상자 , 조정자가 pick한 Reader를 Flag_col에 표시 , Y , N
        dataframe.loc[ (dataframe["USUBJID"]==USUBJID) & (dataframe["READER"]==ADJ_Pick_Analayst) , Flag_col] = "O" 
        dataframe.loc[ (dataframe["USUBJID"]==USUBJID) & (dataframe["READER"]!=ADJ_Pick_Analayst) , Flag_col] = np.nan 



# baeline에서 PCBSLD , PCNSLD , SUMBLD , SUMNLD 등은 np.nan값으로 바꿔주는 함수
# ex)makevalue(df , "SCRN_CT", "PCBSLD" , np.nan)
# baelineNAME : baeline이름(bl or SCRN_CT,,,) , colname : 컬럼이름 , value: 변경 후 값 (여기서는 np.nan)
# dataframe copy를 썼기 때문에 선언해줘야 한다 ex)df.loc[0,"PCBSLD"] = makevalue(df ,0 , "SCRN_CT", "PCBSLD" , 3)

def makevalue(dataframe, baselineNAME , colname , value):
    
    new_dataframe = dataframe.copy(deep = True)
    
    for i in range(len(dataframe)):

        if new_dataframe.loc[i , "VISIT"]==baselineNAME:
            new_dataframe.loc[i , colname] = value
    
    return new_dataframe





# map develop 함수 -> dictionary에 없는 값은 원래의 값을 출력
# ex) map_dict(df , "LAGRADE",LAGRADE_dict ).unique()
def map_dict(dataframe, col , dict_name):
    func = lambda x : dict_name.get(x,x)
    dataframe_new = dataframe[col].map(func , na_action = None)
    
    return dataframe_new


    