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

class First_VISIT_Only(printerror):
    def __init__(self ) :
        self.msg = "첫 방문일을 제외한 다른 방문일 포함되어있습니다. 첫 방문일만 가능합니다."
   




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


#SDTM TU Domain Function
class SDTM_TU:
    def __init__(self, dataframe , _READER) :
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        if len(dataframe["VISIT"].unique()) > 1:
            raise First_VISIT_Only

        # 각 평가자 별 Dataframe 생성
        self.dataframe_copy = dataframe[dataframe["READER"]==_READER].reset_index(drop=True).copy()
        #번호지정
        self.number_list = ["1" , "2", "3", "4", "5"]

        #TU T Lesion 컬럼지정 TUEVALID = READER
        self.columns_list = ["USUBJID" , "VISIT" , "TUEVALID" , "TULOC" , "TULAT" , "TUMETHOD" , "TUDTC", "TUDIR" , "TUPORTOT" , "TUACPTFL"]
        self.df_empty = pd.DataFrame(columns=self.columns_list)
        
        #visit number mapping , 매개변수로 넣어야 될듯
        self.visit_number = {"Screening" : 0 , "W8": 1, "W16": 2, "W24": 3}

        #READER
        self.READER = _READER


    #SDTM TU DOMATIN컬럼으로 정리하는 함수
    #데코레이터 함수
    def columns_cleansing(inputfunc):
        def wrapper_function(*args, **kwargs):
            #컬럼순서
            final = inputfunc(*args, **kwargs)[[
                            "DOMAIN"
                            ,"USUBJID"
                            ,"TULNKID"
                            ,"TUTESTCD"
                            ,"TUTEST"
                            ,"TUORRES"
                            ,"TUSTRESC"
                            ,"TUNAM"
                            ,"TULOC"
                            ,"TULAT"
                            ,"TUMETHOD"
                            ,"TUDIR"
                            ,"TUPORTOT"
                            ,"TUEVAL"
                            ,"TUEVALID"
                            ,"TUACPTFL"
                            ,"VISITNUM"
                            ,"VISIT"
                            ,"TUDTC"]].reset_index(drop=True)
            
            return final
        return wrapper_function
    
    
    """Target Lesion """
    @columns_cleansing
    def TL(self):
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            for z in self.number_list:
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"T_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TULAT_T_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUMETHOD_T_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDTC_T_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDIR_T_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TUPORTOT_T_{}".format(z)],
                                                    self.dataframe_copy.loc[i,"TUACPTFL"]]

        #TUNLKID (T01 , T02...) df_empty길이의 /5 만큼 반복하게 한다.  ex(df_empty길이의 /5가 2라면 , T01 , T02... , T01 , T02...)
        TULNKID_T_list = ["{}-T0{}".format(self.READER , i) for i in list(map(str,range(1,6)))]*int((len(self.df_empty)/5))

        self.df_empty["TULNKID"] = TULNKID_T_list
        
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TULOC"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)

    #default 값 채워주기
        self.df_empty["DOMAIN"] = "TU"
        self.df_empty["TUTESTCD"] = "TUMIDENT"
        self.df_empty["TUTEST"] = "Tumor Identification"
        self.df_empty["TUORRES"] = "TARGET"
        self.df_empty["TUSTRESC"] = "TARGET"
        self.df_empty["TUNAM"] = "Trial Informatics"
        self.df_empty["TUEVAL"] = "INDEPENDENT ASSESSOR"

        return self.df_empty

    """NonTarget"""
    @columns_cleansing
    def NTL(self):
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            for z in self.number_list:
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"NT_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TULAT_NT_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUMETHOD_NT_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDTC_NT_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDIR_NT_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TUPORTOT_NT_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TUACPTFL"]]

        #TUNLKID (T01 , T02...) df_empty길이의 /5 만큼 반복하게 한다.  ex(df_empty길이의 /5가 2라면 , T01 , T02... , T01 , T02...)
        TULNKID_NT_list = ["{}-NT0{}".format(self.READER , i) for i in list(map(str,range(1,6)))]*int((len(self.df_empty)/5))

        self.df_empty["TULNKID"] = TULNKID_NT_list
        
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TULOC"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TU"
        self.df_empty["TUTESTCD"] = "TUMIDENT"
        self.df_empty["TUTEST"] = "Tumor Identification"
        self.df_empty["TUORRES"] = "NON-TARGET"
        self.df_empty["TUSTRESC"] = "NON-TARGET"
        self.df_empty["TUNAM"] = "Trial Informatics"
        self.df_empty["INDEPENDENT ASSESSOR"] = "NON-TARGET"
        self.df_empty["TUEVAL"] = "INDEPENDENT ASSESSOR"

        return self.df_empty

        """New Lesion"""

        