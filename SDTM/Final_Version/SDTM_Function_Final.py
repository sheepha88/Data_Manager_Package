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

class First_VISIT_Exclude(printerror):
    def __init__(self ) :
        self.msg = "첫 방문일이 포함되어있습니다. 첫 방문일 제외해주시기 바랍니다."
   




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
#visit_dict = visit과 visitnumber dict  , ex) {"Screening" : 0 , "W8" : 1 , "Unscheduled" :1.1 , "W16":2 , "Repeat Assessment":201} -> SQL DB에서 끌어온다
class SDTM_TU:
    def __init__(self, dataframe , _READER , visit_dict) :
        
        # 각 평가자 별 Dataframe 생성
        self.dataframe_copy = dataframe[dataframe["READER"]==_READER].reset_index(drop=True).copy()
        #번호지정
        self.number_list = ["1" , "2", "3", "4", "5"]

        #TU T Lesion 컬럼지정 TUEVALID = READER
        self.columns_list = ["USUBJID" , "VISIT" , "TUEVALID" , "TULOC" , "TULAT" , "TUMETHOD" , "TUDTC", "TUDIR" , "TUPORTOT" , "TUACPTFL"]
        self.df_empty = pd.DataFrame(columns=self.columns_list)
        
        #visit number mapping 
        self.visit_number = visit_dict

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
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        if len(self.dataframe_copy["VISIT"].unique()) > 1:
            raise First_VISIT_Only
        if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
            raise First_VISIT_Only
            
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
    @columns_cleansing
    def NL(self):
        #dataframe의 방문일이 첫 방문일만 있다면 error발생
        if list(self.visit_number.keys())[0] in list(self.dataframe_copy["VISIT"].unique()):
            raise First_VISIT_Exclude
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            for z in self.number_list:
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"NEW_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TULAT_NEW_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUMETHOD_NEW_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDTC_NEW_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDIR_NEW_{}".format(z)] ,
                                                    self.dataframe_copy.loc[i,"TUPORTOT_NEW_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUACPTFL"]]


        #TUNLKID (NEW01 , NEW02...) df_empty길이의 /5 만큼 반복하게 한다.  ex(df_empty길이의 /5가 2라면 , NEW01 , NEW02... , NEW01 , NEW02...)
        TULNKID_NEW_list = ["{}-NEW0{}".format(self.READER , i) for i in list(map(str,range(1,6)))]*int((len(self.df_empty)/5))


        self.df_empty["TULNKID"] = TULNKID_NEW_list
        
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TULOC"].notnull()]    

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        
        #New Lesio 중복되는 행 제거 : drop duplicates (dupli_drop_col 리스트 기준으로)
        #New Lesion 중에서 
        self.dupli_drop_col = ["USUBJID", "TULOC"  , "TULAT"  , "TUMETHOD"  ,  "TUDIR"  , "TUPORTOT"]
        self.df_empty = self.df_empty.drop_duplicates(subset = self.dupli_drop_col)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TU"
        self.df_empty["TUTESTCD"] = "TUMIDENT"
        self.df_empty["TUTEST"] = "Tumor Identification"
        self.df_empty["TUORRES"] = "NEW"
        self.df_empty["TUSTRESC"] = "NEW"
        self.df_empty["TUNAM"] = "Trial Informatics"
        self.df_empty["TUEVAL"] = "INDEPENDENT ASSESSOR"

                            
        return self.df_empty
        


#############################################################################################################################################
#SDTM TR Domain Function
#visit_group = visit과 visitgroup dict  , ex) {"Screening" : R1-A1 , "W8" : "R1-A2" , "Unscheduled" :"R1-B2" , "W16":"R1-A3" , "Repeat Assessment":"R1-C1"} -> SQL DB에서 끌어온다
#SDTM TU상속
class SDTM_TR(SDTM_TU):
    def __init__(self, dataframe, _READER, visit_dict , visit_group):
        super().__init__( dataframe , _READER, visit_dict )
     
        #TU T Lesion 컬럼지정 TUEVALID = READER
        self.columns_list = ["USUBJID" , "VISIT" , "TREVALID" ,  "TRMETHOD" , "TRDTC", "TRACPTFL" , "TRORRES" ,  "TRSTRESC" , "TRSTRESN","TRSTAT","TRREASND" ]
        
        #visit group mapping
        self.TRLNKGRP_mapping = visit_group

        #TRLNKGRP_mapping dict 에 Reader 값 추가하기 위해 재정의 ex) R2-A1
        self.TRLNKGRP_mapping = dict(zip(self.TRLNKGRP_mapping.keys() , [_READER+"-"+i for i in self.TRLNKGRP_mapping.values()]))


    #SDTM TR DOMATIN컬럼으로 정리하는 함수
    #데코레이터 함수
    def columns_cleansing(inputfunc):
        def wrapper_function(*args, **kwargs):
            #컬럼순서
            final = inputfunc(*args, **kwargs)[[
                            "DOMAIN"
                            ,"USUBJID"
                            ,"TRGRPID"
                            ,"TRLNKGRP"
                            ,"TRLNKID"
                            ,"TRTESTCD"
                            ,"TRTEST"
                            ,"TRORRES"
                            ,"TRORRESU"
                            ,"TRSTRESC"
                            ,"TRSTRESN"
                            ,"TRSTRESU"
                            ,"TRSTAT"
                            ,"TRREASND"
                            ,"TRNAM"
                            ,"TRMETHOD"
                            ,"TREVAL"
                            ,"TREVALID"
                            ,"TRACPTFL"
                            ,"VISITNUM"
                            ,"VISIT"
                            ,"TRDTC"]].reset_index(drop=True)
            
            return final
        return wrapper_function
    
    
    """Target Lesion DIAMETER"""
    @columns_cleansing
    def DIAMETER(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            for z in self.number_list:
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [
                                                    self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"TUMETHOD_T_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDTC_T_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUACPTFL"],
                                                    self.dataframe_copy.loc[i,"TRORRES_T_{}".format(z)],
                                                    self.dataframe_copy.loc[i,"TRORRES_T_{}".format(z)],
                                                    self.dataframe_copy.loc[i,"TRORRES_T_{}".format(z)],
                                                    "NOT DONE" if self.dataframe_copy.loc[i,"TRORRES_NE_T_{}".format(z)] is "NE" else np.nan,
                                                    self.dataframe_copy.loc[i,"TRORRES_CMT_T_{}".format(z)]
                                                    ]

        #TUNLKID (T01 , T02...) df_empty길이의 /5 만큼 반복하게 한다.  ex(df_empty길이의 /5가 2라면 , T01 , T02... , T01 , T02...)
        TRLNKID_T_list = ["{}-T0{}".format(self.READER , i) for i in list(map(str,range(1,6)))]*int((len(self.df_empty)/5))

        self.df_empty["TRLNKID"] = TRLNKID_T_list
        
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "TARGET"
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "DIAMETER"
        self.df_empty["TRTEST"] = "Diameter"
        self.df_empty["TRORRESU"] = "mm"
        self.df_empty["TRSTRESU"] = "mm"

        return self.df_empty


    """Non-Target Lesion STATUS"""
    @columns_cleansing
    def STATUS(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            for z in self.number_list:
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [
                                                    self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"TUMETHOD_NT_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUDTC_NT_{}".format(z)] , 
                                                    self.dataframe_copy.loc[i,"TUACPTFL"],
                                                    self.dataframe_copy.loc[i,"TUMSTATE_NT_{}".format(z)],
                                                    self.dataframe_copy.loc[i,"TUMSTATE_NT_{}".format(z)],
                                                    np.nan,#TRSTRESC : NonTarget 에서는 값이 없는 컬럼
                                                    # Status가 NE면 Non done
                                                    "NOT DONE" if self.dataframe_copy.loc[i,"TUMSTATE_NT_{}".format(z)] is "NE" else np.nan,
                                                    self.dataframe_copy.loc[i,"TUMSTATE_CMT_NT_{}".format(z)]
                                                    ]

        #TUNLKID (T01 , T02...) df_empty길이의 /5 만큼 반복하게 한다.  ex(df_empty길이의 /5가 2라면 , T01 , T02... , T01 , T02...)
        TRLNKID_T_list = ["{}-NT0{}".format(self.READER , i) for i in list(map(str,range(1,6)))]*int((len(self.df_empty)/5))

        self.df_empty["TRLNKID"] = TRLNKID_T_list
        
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "NON-TARGET"
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "TUMSTATE"
        self.df_empty["TRTEST"] = "Tumor State"
        self.df_empty["TRORRESU"] = np.nan
        self.df_empty["TRSTRESN"] = np.nan
        self.df_empty["TRSTRESU"] = np.nan

        return self.df_empty



#SDTM TR_ Domain Function
#visit_group = visit과 visitgroup dict  , ex) {"Screening" : R1-A1 , "W8" : "R1-A2" , "Unscheduled" :"R1-B2" , "W16":"R1-A3" , "Repeat Assessment":"R1-C1"} -> SQL DB에서 끌어온다
#SDTM TU상속
class SDTM_TR_CAL(SDTM_TR):
    def __init__(self, dataframe, _READER, visit_dict, visit_group):
        super().__init__(dataframe, _READER, visit_dict, visit_group)

        self.columns_list = ["USUBJID" , "VISIT" , "TREVALID" , "TRACPTFL" , "TRORRES" ,  "TRSTRESC" , "TRSTRESN" ]

    #SDTM TR DOMATIN컬럼으로 정리하는 함수
    #데코레이터 함수
    def columns_cleansing(inputfunc):
        def wrapper_function(*args, **kwargs):
            #컬럼순서
            final = inputfunc(*args, **kwargs)[[
                            "DOMAIN"
                            ,"USUBJID"
                            ,"TRGRPID"
                            ,"TRLNKGRP"
                            ,"TRLNKID"
                            ,"TRTESTCD"
                            ,"TRTEST"
                            ,"TRORRES"
                            ,"TRORRESU"
                            ,"TRSTRESC"
                            ,"TRSTRESN"
                            ,"TRSTRESU"
                            ,"TRSTAT"
                            ,"TRREASND" 
                            ,"TRNAM"
                            ,"TRMETHOD"
                            ,"TREVAL"
                            ,"TREVALID"
                            ,"TRACPTFL"
                            ,"VISITNUM"
                            ,"VISIT"                             
                            ,"TRDTC"]].reset_index(drop=True)
            
            return final
        return wrapper_function
    
    
    """Target Lesion SUMDIAM"""
    @columns_cleansing
    def SUMDIAM(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            
            #cnt번째대로 각 컬럼값들 끌어온다
            cnt+=1
            self.df_empty.loc[cnt,self.columns_list] = [
                                                self.dataframe_copy.loc[i,"USUBJID"] ,
                                                self.dataframe_copy.loc[i,"VISIT"] ,
                                                self.dataframe_copy.loc[i,"READER"] ,                                                     
                                                self.dataframe_copy.loc[i,"TUACPTFL"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"]
                                                ]
    
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "TARGET"
        self.df_empty["TRLNKID"] = np.nan
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "SUMDIAM"
        self.df_empty["TRTEST"] = "Sum of Diameter"
        self.df_empty["TRORRESU"] = "mm"
        self.df_empty["TRSTRESU"] = "mm"
        self.df_empty["TRSTAT"] = np.nan
        self.df_empty["TRREASND"] = np.nan
        self.df_empty["TRMETHOD"] = np.nan
        self.df_empty["TRDTC"] = np.nan


        return self.df_empty
        

    """Target Lesion ACNSD"""
    @columns_cleansing
    def ACNSD(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            
            #cnt번째대로 각 컬럼값들 끌어온다
            cnt+=1
            self.df_empty.loc[cnt,self.columns_list] = [
                                                self.dataframe_copy.loc[i,"USUBJID"] ,
                                                self.dataframe_copy.loc[i,"VISIT"] ,
                                                self.dataframe_copy.loc[i,"READER"] ,                                                     
                                                self.dataframe_copy.loc[i,"TUACPTFL"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"]-self.dataframe_copy.loc[i,"SUMNSD"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"]-self.dataframe_copy.loc[i,"SUMNSD"],
                                                self.dataframe_copy.loc[i,"SUMDIAM"]-self.dataframe_copy.loc[i,"SUMNSD"]
                                                ]

        #ACNSD = baseline 제외
        self.df_empty = self.df_empty[ self.dataframe_copy["VISIT"]!=list(self.visit_number.keys())[0] ]
    
        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "TARGET"
        self.df_empty["TRLNKID"] = np.nan
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "ACNSD"
        self.df_empty["TRTEST"] = "Absolute Change From Nadir in Sum of Diameters"
        self.df_empty["TRORRESU"] = "mm"
        self.df_empty["TRSTRESU"] = "mm"
        self.df_empty["TRSTAT"] = np.nan
        self.df_empty["TRREASND"] = np.nan
        self.df_empty["TRMETHOD"] = np.nan
        self.df_empty["TRDTC"] = np.nan


        return self.df_empty


    """Target Lesion PCBSD"""
    @columns_cleansing
    def PCBSD(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            
            #cnt번째대로 각 컬럼값들 끌어온다
            cnt+=1
            self.df_empty.loc[cnt,self.columns_list] = [
                                                self.dataframe_copy.loc[i,"USUBJID"] ,
                                                self.dataframe_copy.loc[i,"VISIT"] ,
                                                self.dataframe_copy.loc[i,"READER"] ,                                                     
                                                self.dataframe_copy.loc[i,"TUACPTFL"],
                                                self.dataframe_copy.loc[i,"PCBSD"],
                                                self.dataframe_copy.loc[i,"PCBSD"],
                                                self.dataframe_copy.loc[i,"PCBSD"]
                                                ]

        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #ACNSD = baseline 제외
        self.df_empty = self.df_empty[ self.dataframe_copy["VISIT"]!=list(self.visit_number.keys())[0] ]
          
        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "TARGET"
        self.df_empty["TRLNKID"] = np.nan
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "PCBSD"
        self.df_empty["TRTEST"] = "Percent Change From Baseline in sum of Diameters"
        self.df_empty["TRORRESU"] = "%"
        self.df_empty["TRSTRESU"] = "%"
        self.df_empty["TRSTAT"] = np.nan
        self.df_empty["TRREASND"] = np.nan
        self.df_empty["TRMETHOD"] = np.nan
        self.df_empty["TRDTC"] = np.nan


        return self.df_empty


    """Target Lesion PCNSD"""
    @columns_cleansing
    def PCNSD(self):
        #dataframe의 방문일이 첫 방문일 이외의 다른 방문일이 포함되어있다면 error발생
        # if len(self.dataframe_copy["VISIT"].unique()) > 1:
        #     raise First_VISIT_Only
        # if list(self.dataframe_copy["VISIT"].unique())[0] !=  list(self.visit_number.keys())[0]:
        #     raise First_VISIT_Only

        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            
            #cnt번째대로 각 컬럼값들 끌어온다
            cnt+=1
            self.df_empty.loc[cnt,self.columns_list] = [
                                                self.dataframe_copy.loc[i,"USUBJID"] ,
                                                self.dataframe_copy.loc[i,"VISIT"] ,
                                                self.dataframe_copy.loc[i,"READER"] ,                                                     
                                                self.dataframe_copy.loc[i,"TUACPTFL"],
                                                self.dataframe_copy.loc[i,"PCNSD"],
                                                self.dataframe_copy.loc[i,"PCNSD"],
                                                self.dataframe_copy.loc[i,"PCNSD"]
                                                ]

        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["TRORRES"].notnull()]

        #ACNSD = baseline 제외
        self.df_empty = self.df_empty[ self.dataframe_copy["VISIT"]!=list(self.visit_number.keys())[0] ]
          
        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["TRLNKGRP"] = self.df_empty["VISIT"].map(self.TRLNKGRP_mapping)

        #default 값 채워주기
        self.df_empty["DOMAIN"] = "TR"
        self.df_empty["TRGRPID"] = "TARGET"
        self.df_empty["TRLNKID"] = np.nan
        self.df_empty["TRNAM"] = "Trial Informatics"
        self.df_empty["TREVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["TRTESTCD"] = "PCNSD"
        self.df_empty["TRTEST"] = "Percent Change From Nadir in sum of Diameters"
        self.df_empty["TRORRESU"] = "%"
        self.df_empty["TRSTRESU"] = "%"
        self.df_empty["TRSTAT"] = np.nan
        self.df_empty["TRREASND"] = np.nan
        self.df_empty["TRMETHOD"] = np.nan
        self.df_empty["TRDTC"] = np.nan


        return self.df_empty



#############################################################################################################################################
#SDTM RS Domain Function
#visit_group = visit과 visitgroup dict  , ex) {"Screening" : R1-A1 , "W8" : "R1-A2" , "Unscheduled" :"R1-B2" , "W16":"R1-A3" , "Repeat Assessment":"R1-C1"} -> SQL DB에서 끌어온다

class SDTM_RS(SDTM_TR):
    def __init__(self, dataframe, _READER, visit_dict , visit_group):
        super().__init__( dataframe , _READER, visit_dict  , visit_group)

        # #daframe 지정 - READER , Target Lesion Indicator
        self.dataframe_copy = dataframe[(dataframe["READER"]==_READER) ].reset_index(drop=True).copy()
     
        #TU T Lesion 컬럼지정 TUEVALID = READER
        self.columns_list = ["USUBJID" , "VISIT" , "RSEVALID"  , "RSDTC", "RSACPTFL" , "RSORRES" ,  "RSSTRESC" ,"RSSTAT","RSREASND", "RSCOMM"  ]

        #RSLNKGRP_mapping dict 에 Reader 값 추가하기 위해 재정의 ex) R2-A1
        self.RSLNKGRP_mapping = visit_group
        self.RSLNKGRP_mapping = dict(zip(self.RSLNKGRP_mapping.keys() , [_READER+"-"+i for i in self.RSLNKGRP_mapping.values()]))


    #SDTM RS DOMATIN컬럼으로 정리하는 함수
    #데코레이터 함수
    def columns_cleansing(inputfunc):
        def wrapper_function(*args, **kwargs):
            #컬럼순서
            final = inputfunc(*args, **kwargs)[[
                            "DOMAIN"
                            ,"USUBJID"
                            ,"RSLNKGRP"
                            ,"RSTESTCD"
                            ,"RSTEST"
                            ,"RSCAT"
                            ,"RSORRES"
                            ,"RSSTRESC"
                            ,"RSSTAT"
                            ,"RSREASND"
                            ,"RSNAM"
                            ,"RSEVAL"
                            ,"RSEVALID"
                            ,"RSCOMM"
                            ,"RSACPTFL"
                            ,"VISITNUM"
                            ,"VISIT"
                            ,"RSDTC"]].reset_index(drop=True)
            
            return final
        return wrapper_function



    """Target Response"""
    @columns_cleansing
    def Target_Response(self):
        # self.dataframe_copy = self.dataframe_copy[(self.dataframe_copy["TRIND"]=="Yes")].reset_index(drop=True).copy()
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            # Lesion이 Yes인 경우에만
            if self.dataframe_copy.loc[i,"TRIND"]=="Yes":
            #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"RSDTC_T"] , 
                                                    self.dataframe_copy.loc[i,"TUACPTFL"],
                                                    self.dataframe_copy.loc[i,"TRGRESP_RS"],
                                                    self.dataframe_copy.loc[i,"TRGRESP_RS"],
                                                    # Target Response가 NE면 Non done
                                                    "NOT DONE" if self.dataframe_copy.loc[i,"TRGRESP_RS"] is "NE" else np.nan,
                                                    # Target Response NE 면 comment 기재
                                                    self.dataframe_copy.loc[i,"TRGRESP_CMT"] if self.dataframe_copy.loc[i,"TRGRESP_RS"] is "NE" else np.nan,
                                                    self.dataframe_copy.loc[i,"TRGRESP_CMT"]
                                                    ]

        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["RSORRES"].notnull()]
        

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["RSLNKGRP"] = np.nan

    #default 값 채워주기
        self.df_empty["DOMAIN"] = "RS"
        self.df_empty["RSNAM"] = "Trial Informatics"
        self.df_empty["RSEVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["RSTESTCD"] = "TRGRESP"
        self.df_empty["RSTEST"] = "Target Response"
        self.df_empty["RSCAT"] = "RECIST 1.1"
     

        return self.df_empty



    """Non-Target Response"""
    @columns_cleansing
    def Non_Target_Response(self):
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            # Lesion이 Yes인 경우에만
            if self.dataframe_copy.loc[i,"NTRIND"]=="Yes":
                #cnt번째대로 각 컬럼값들 끌어온다
                cnt+=1
                self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                                    self.dataframe_copy.loc[i,"VISIT"] ,
                                                    self.dataframe_copy.loc[i,"READER"] , 
                                                    self.dataframe_copy.loc[i,"RSDTC_NT"] , 
                                                    self.dataframe_copy.loc[i,"TUACPTFL"],
                                                    self.dataframe_copy.loc[i,"NTRGRESP_RS"],
                                                    self.dataframe_copy.loc[i,"NTRGRESP_RS"],
                                                    # Target Response가 NE면 Non done
                                                    "NOT DONE" if self.dataframe_copy.loc[i,"NTRGRESP_RS"] is "NE" else np.nan,
                                                    # Target Response NE 면 comment 기재
                                                    self.dataframe_copy.loc[i,"NTRGRESP_CMT"] if self.dataframe_copy.loc[i,"NTRGRESP_RS"] is "NE" else np.nan,
                                                    self.dataframe_copy.loc[i,"NTRGRESP_CMT"]
                                                    ]

        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["RSORRES"].notnull()]
        

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["RSLNKGRP"] = np.nan
        #default 값 채워주기
        self.df_empty["DOMAIN"] = "RS"
        self.df_empty["RSNAM"] = "Trial Informatics"
        self.df_empty["RSEVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["RSTESTCD"] = "NTRGRESP"
        self.df_empty["RSTEST"] = "Non-target Response"
        self.df_empty["RSCAT"] = "RECIST 1.1"
     

        return self.df_empty


    """Overall Response"""
    @columns_cleansing
    def Overall_Response(self):
        #cnt = df_empty의 차례로 append하기 위해 -1부터 시작 그래야 첫번째때 0(-1+1)번째 행에 append 된다
        cnt = -1
        for i in range(len(self.dataframe_copy)):
            # Lesion이 Yes인 경우에만
            # if self.dataframe_copy.loc[i,"NTRIND"]=="Yes":
                #cnt번째대로 각 컬럼값들 끌어온다
            cnt+=1
            self.df_empty.loc[cnt,self.columns_list] = [self.dataframe_copy.loc[i,"USUBJID"] ,
                                        self.dataframe_copy.loc[i,"VISIT"] ,
                                        self.dataframe_copy.loc[i,"READER"] , 
                                        self.dataframe_copy.loc[i,"RSDTC_RS"] , 
                                        self.dataframe_copy.loc[i,"TUACPTFL"],
                                        self.dataframe_copy.loc[i,"OVRLRESP_RS"],
                                        self.dataframe_copy.loc[i,"OVRLRESP_RS"],
                                        # Target Response가 NE면 Non done
                                        "NOT DONE" if self.dataframe_copy.loc[i,"OVRLRESP_RS"] is "NE" else np.nan,
                                        # Target Response NE 면 comment 기재
                                        self.dataframe_copy.loc[i,"OVRLRESP_CMT"] if self.dataframe_copy.loc[i,"OVRLRESP_RS"] is "NE" else np.nan,
                                        self.dataframe_copy.loc[i,"OVRLRESP_CMT"]
                                        ]

        #null값 제외
        self.df_empty = self.df_empty[self.df_empty["RSORRES"].notnull()]
        

        #visit mapping
        self.df_empty["VISITNUM"] = self.df_empty["VISIT"].map(self.visit_number)
        self.df_empty["RSLNKGRP"] = self.df_empty["VISIT"].map(self.RSLNKGRP_mapping)
        #default 값 채워주기
        self.df_empty["DOMAIN"] = "RS"
        self.df_empty["RSNAM"] = "Trial Informatics"
        self.df_empty["RSEVAL"] = "INDEPENDENT ASSESSOR"
        self.df_empty["RSTESTCD"] = "OVRLRESP"
        self.df_empty["RSTEST"] = "Overall Response"
        self.df_empty["RSCAT"] = "RECIST 1.1"
     

        return self.df_empty
        
        

        