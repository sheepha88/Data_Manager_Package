import numpy as np
import pandas as pd
import datetime
import warnings
import openpyxl
warnings.filterwarnings("ignore")


# 오류 메세지
class printerror(Exception):
    def __init__(self, msg) :
          self.msg = msg
    def __str__(self):
          return self.msg

class Baselineerror(printerror):
    def __init__(self,Baselinename ) :
        self.msg = ("\"{}\" do not match with baselinename of dataframe ".format(Baselinename ))

class USUBJIDerror(printerror):
    def __init__(self,USUBJID ) :
        self.msg = ("\"{}\" do not exist in USUBJID of dataframe ".format(USUBJID ))


class ADJ_PICKerror(printerror): 
    def __init__(self,USUBJID ) : 
        self.msg = ( "Subject ID : \"{}\" 조정자값이 두 평가자 값과 달라 확인요망".format(USUBJID))


#SDTM Function
class SDTM:
    def __init__(self) :
          pass

### 조정자 pick 오류 검토 함수
# ADJ_PICK(df , "01S306" , "Baseline (1st scan)" , "ADJUDICATOR" , "Analyst#1" , "Analyst#2" ,"TUACPTFL" ,  ["TRGOC_1","TRGOCOT_1","TRGLD_1"])
# 1. raw_dataframe에서 해당 대상자의 baseline에서 columns를 기준으로 ADJ와 Analyst를 비교하여 ADJ가 누굴 택했는지 확인(인자 = ADJ_Pick_Analayst)
# 2. ADJ 와 선택된 Analyst들만 있는 테이블을 뽑아내고 , 조정자 행과 선택된 Analyst행의 columns값들을 비교하여 하나라도 틀린 행이 있으면 출력

    def Flag_col(dataframe, USUBJID , Baselinename , ADJUDICATOR , Analyst_1 , Analyst_2 , Flag_col , columns):
        try: 
            #해당 대상자의 baseline만 뽑아낸 테이블
            baseline_Dataframe = dataframe[ (dataframe["USUBJID"]==USUBJID) & (dataframe["VISIT"]==Baselinename)].reset_index(drop=True)
            
            #AJD의 columns값
            ADJ_values = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==ADJUDICATOR].index)[0] , columns]

            #analyst#1의 columns값
            Analyst_1_values = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_1].index)[0] , columns]

            #analyst#2의 columns값
            Analyst_2_values = baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_2].index)[0] , columns]
            
            # 조정자의 columns값과 Analyst#1의 columns값이 baseline에서 같다면 analyst#1을 출력해라
            if ADJ_values.equals(Analyst_1_values):
                ADJ_Pick_Analayst = Analyst_1

            # 조정자의 columns값과 Analyst#2의 columns값이 baseline에서 같다면 analyst#2을 출력해라        
            elif ADJ_values.equals(Analyst_2_values):
                ADJ_Pick_Analayst = Analyst_2

            # 헤당 대상자 , 조정자가 pick한 Reader를 Flag_col에 표시 , Y , N
            dataframe.loc[ (dataframe["USUBJID"]==USUBJID) & (dataframe["READER"]==ADJ_Pick_Analayst) , Flag_col] = "Y" 
            dataframe.loc[ (dataframe["USUBJID"]==USUBJID) & (dataframe["READER"]!=ADJ_Pick_Analayst) , Flag_col] = "N" 

            #두 평가자의 값이 모두 똑같아서 조정자 pick을 마킹할 수 없는 경우
            if Analyst_1_values.equals(Analyst_2_values):
                dataframe.loc[ (dataframe["USUBJID"]==USUBJID)  , Flag_col] = "두 평가자의 값이 모두 같아 Follow up확인 요망"

            return dataframe 

        except:
            #error 출력
            #basline이 dataframe에 없는 경우
            if Baselinename not in list(dataframe["VISIT"].unique()):
                raise Baselineerror(Baselinename)

            #대상자가 dataframe에 없는 경우
            if USUBJID not in list(dataframe["USUBJID"].unique()):
                raise USUBJIDerror(USUBJID)

            #조정자 값이 두 평가자 값과 달라 확인이 필요한 경우
            if not ADJ_values.equals(Analyst_1_values):
                if not ADJ_values.equals(Analyst_2_values):
                    raise ADJ_PICKerror(USUBJID)
