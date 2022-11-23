import numpy as np
import pandas as pd
import datetime
import warnings
import openpyxl
warnings.filterwarnings("ignore")



# Modality와 Scan Type에 따라 Date가 잘 입력 되었는가     2022.10.25
# -> SCAN TYPE의 Date가 잘못 기재된 경우
# ex) CT SCAN , Chest 이면 Form 상단의 영상촬영일자의 CT-Chest Date와 동일해야 한다.
def ScanDataCheck(dataframe):
    result_dataframe = pd.dataframe(coloums=dataframe.columns)
    result_dataframe['DM_CMT']=np.nan
    # TUMETHOD_NT_i : CT,MRI,Other  , TUIMG_NT_i : Chest,Abdomen/Pelvis,Other , TUDTC_NT_i , 
    for i in range(len(dataframe)):
        for j in range(1,6):
            modality = "TUMETHOD_NT_"+str(j)
            scan_type = "TUIMG_NT_"+str(j)
            scan_date = "TUDTC_NT_"+str(j)
            if (dataframe.loc[i,modality]!=None and dataframe.loc[i,scan_type]!=None):
                if dataframe.loc[i,scan_date] == None:
                    new_line=dataframe.loc[i,:]
                    new_line["DM_CMT"] = "날짜를 불러오지 못한 경우 Non-Target Lession{}번째".format(j)
                    result_dataframe.append(new_line)
                else:
                    original_type = "TUDTC_"
                    if not dataframe.loc[i,modality] in ["CT","MRI"]:
                        original_type+="OT_OT"
                    else:
                        if dataframe.loc[i,modality]=="CT_":
                            original_type+="CT"
                        else:
                            original_type+="MRI_"

                        if dataframe.loc[i,scan_type]=="Chest":
                            original_type+="CHEST"
                        elif dataframe.loc[i,scan_type]=="Abdomen/Pelvis":
                            original_type+="ABD"
                        else:
                            original_type+="OT"
                    
                    if dataframe.loc[i,original_type]==None:
                        new_line=dataframe.loc[i,:]
                        new_line["DM_CMT"] = "옵션을 잘못 선택해서 날짜 값이 없는 타입을 선택한 경우 Non-Target Lession {}번째".format(j)
                        result_dataframe.append(new_line)
                
    return result_dataframe      

# Status가 Present이면 반드시 Non-CR/Non-PD 여아한다.     2022-10-25
# Non target 에서 present인데 Non CR Non PD가 아닌 경우를 검토하는 함수  
# Status가 Present이면 반드시 Non-CR/Non-PD 여아한다. // col_status를 각각 순회하여 Present인데 Non CR Non PD인지 검토 
# ex) NonTargetResponse(df_NTL , "Non-CR/Non-PD" , "NTRGRESP" , "Present" , col_status=["TUMSTATE_NT_1" ,"TUMSTATE_NT_2" ,"TUMSTATE_NT_3" , "TUMSTATE_NT_4" , "TUMSTATE_NT_5"] , "Unequivocal progression" )
def NonTargetResponse_NonCR_NonPD(dataframe , NonTargetResponse , NonTargetResponse_col , Status_response , col_status , Lesion_status ):

    df_frame = pd.DataFrame(columns = dataframe.columns)
    df_frame["DM_CMT"] = np.nan


    for i in range(len(dataframe)):

        option1 = Status_response in list(dataframe.loc[i,col_status])
        option2 = dataframe.loc[i , NonTargetResponse_col]!=NonTargetResponse
        option3 = not Lesion_status in list(dataframe.loc[i,col_status])   # "Unequivocal progression" 입력시 철자확인 할 것  

        if option1 and option2 and option3:
            
            df_empty = dataframe.loc[i ,:]
            df_empty["DM_CMT"] = "Lesion Status가 {} 인데 , Response가 {}가 아닌 경우".format(Status_response , NonTargetResponse)

            # 행을 추가하면서 df_NTL_NTRGRESP_incorrect 에 저장
            df_frame = df_frame.append(df_empty)

    return df_frame

# Non Target Response PD 검토 함수
# Status 중에서 하나라도 Unequivocal Progression 이면 출력
# ex) NonTargetResponse(df_NTL , "PD" , "NTRGRESP" , "Unequivocal Progression" , col_status=["TULSTAT_1" ,"TULSTAT_2" ,"TULSTAT_3" , "TULSTAT_4" , "TULSTAT_5"])
def NonTargetResponse_PD(dataframe , NonTargetResponse , NonTargetResponse_col , Status_response , col_status  ):

    # dataframe: NTL
    # NonTargetResponse : PD , PR , ...
    # NonTargetResponse_col : NRGRESP
    # Status_response : Absent , Present,..
    # col_status : TUMSTATE_NT_1 , ....
    
    df_frame = pd.DataFrame(columns = dataframe.columns)
    df_frame["DM_CMT"] = np.nan


    # df_NTL의 컬럼으로 이루어진 빈 데이터프레임 생성
    df_empty = pd.DataFrame(columns = dataframe.columns)
    # DM코멘트 추가
    # df_empty["DM_CMT"] = np.nan

    #Non Target Status를 리스트로
    for i in range(len(dataframe)):
        if Status_response in list(dataframe.loc[i,col_status]):
            if dataframe.loc[i , NonTargetResponse_col]!=NonTargetResponse:
                df_empty = dataframe.loc[i ,:]
                df_empty["DM_CMT"] = "Lesion Status가 {} 인데 , Response가 {}가 아닌 경우".format(Status_response , NonTargetResponse)

                #행을 추가하면서 df_NTL_NTRGRESP_incorrect 에 저장
                df_frame = df_frame.append(df_empty)

    return df_frame



# Non Target Response CR 검토 함수
# Status 중에서 하나라도 Unequivocal Progression 이면 출력
# ex) NonTargetResponse_CR(df_NTL , "CR" , "NTRGRESP" , "Absent" , col_status=["TULSTAT_1" ,"TULSTAT_2" ,"TULSTAT_3" , "TULSTAT_4" , "TULSTAT_5"])
def NonTargetResponse_CR(dataframe , NonTargetResponse , NonTargetResponse_col , Status_response , col_status  ):

    #dataframe: NTL
    #NonTargetResponse : PD , PR , ...
    #NonTargetResponse_col : NRGRESP
    #Status_response : Absent , Present,..
    #col_status : TUMSTATE_NT_1 , ....
    
    df_frame = pd.DataFrame(columns = dataframe.columns)
    df_frame["DM_CMT"] = np.nan


    # df_NTL의 컬럼으로 이루어진 빈 데이터프레임 생성
    df_empty = pd.DataFrame(columns = dataframe.columns)
    # DM코멘트 추가
    # df_empty["DM_CMT"] = np.nan

    #Non Target Status를 리스트로
    for i in range(len(dataframe)):

        #nan제외한 status리스트 생성
        status_list = list(dataframe.loc[i,col_status])
        status_list = [z for z in status_list if pd.notnull(z)]


        #status_list가 모두 nan인 경우는 제외하고 진행
        if len(status_list)!=0:
            #status 리스트에 있는 요소들이 모두 absent이면 진행
            if all(Status_response ==x for x in status_list):

                #모두 absent인데 CR이 아닌경우 출력
                if dataframe.loc[i , NonTargetResponse_col]!=NonTargetResponse:
                    df_empty = dataframe.loc[i ,:]
                    df_empty["DM_CMT"] = "Lesion Status가 모두 {} 인데 , Response가 {}가 아닌 경우".format(Status_response , NonTargetResponse)

                    #행을 추가하면서 df_NTL_NTRGRESP_incorrect 에 저장
                    df_frame = df_frame.append(df_empty)

    return df_frame
    

###조정자 pick 오류 검토 함수
#ADJ_PICK(df , "01S306" , "Baseline (1st scan)" , "ADJUDICATOR" , "Analyst#1" , "Analyst#2" , ["TRGOC_1","TRGOCOT_1","TRGLD_1"])
# 1. raw_dataframe에서 해당 대상자의 baseline에서 columns를 기준으로 ADJ와 Analyst를 비교하여 ADJ가 누굴 택했는지 확인(인자 = ADJ_Pick_Analayst)
# 2. ADJ 와 선택된 Analyst들만 있는 테이블을 뽑아내고 , 조정자 행과 선택된 Analyst행의 columns값들을 비교하여 하나라도 틀린 행이 있으면 출력

def ADJ_PICK(dataframe, USUBJID , Baselinename , ADJUDICATOR , Analyst_1 , Analyst_2 , columns):
    
    #해당 대상자의 baseline만 뽑아낸 테이블
    baseline_Dataframe = dataframe[ (dataframe["USUBJID"]==USUBJID) & (dataframe["VISIT"]==Baselinename)].reset_index(drop=True)
    
    #해당 대상자의 전체 visit 뽑아낸 테이블
    visit_Dataframe = dataframe[ (dataframe["USUBJID"]==USUBJID)].reset_index(drop=True)
    
  
    # 조정자의 columns값과 Analyst#1의 columns값이 baseline에서 같다면 analyst#1을 출력해라
    if baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==ADJUDICATOR].index)[0] , columns].equals\
        (baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_1].index)[0] , columns]):
            ADJ_Pick_Analayst = Analyst_1
            
    
    elif baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==ADJUDICATOR].index)[0] , columns].equals\
        (baseline_Dataframe.loc[list(baseline_Dataframe[baseline_Dataframe["READER"]==Analyst_2].index)[0] , columns]):
            ADJ_Pick_Analayst = Analyst_2
    
    
    #baseline에서 조정자가 pick한 Analyst와 조정자값만으로 이루어진 테이블 생성
    visit_Dataframe = visit_Dataframe[visit_Dataframe["READER"].isin([ADJUDICATOR ,ADJ_Pick_Analayst ])].reset_index(drop=True)
    
    
    #반복문으로 격수로 (ADJ , Analyst#) 비교해서 컬럼중 데이터값이 하나라도 틀리면 조정자 , Analyst행 출력
    result = pd.DataFrame()
    for i in range(0,len(visit_Dataframe),2):
        if not visit_Dataframe.loc[i,columns].equals(visit_Dataframe.loc[i+1,columns]):
            result = result.append([visit_Dataframe.loc[i,:] ,visit_Dataframe.loc[i+1,:] ])
            
        else:
            pass
        
    return result 
    
    
    
        
#map develop 함수 -> dictionary에 없는 값은 원래의 값을 출력
# ex) map_dict(df , "LAGRADE",LAGRADE_dict ).unique()
def map_dict(dataframe, col , dict_name):
    func = lambda x : dict_name.get(x,x)
    dataframe_new = dataframe[col].map(func , na_action = None)
    
    return dataframe_new
    


# # 배치리스트와 export한 data 일치하는지 확인-배치리스트의 각 대상자 visit정보 리스트화 시키는 과정
# ex) visit_extract(df_list , "Subject No","S32-13013")
# 
# 1)
def visit_extract(dataframe_batchlist , col ,  subjectNO ):
    
    #dataframe_batchlist_column_list 중 Baseline~EOT까지 범위설정 , 보통 0번쨰가 USUBJID라 1번째 부터 시작
    dataframe_batchlist_column_list = dataframe_batchlist.columns[1:]  
    
    #return 결과 담을 list 생성
    visit_result = []
    
    for z in dataframe_batchlist_column_list:
        if pd.notnull(dataframe_batchlist[dataframe_batchlist[col] ==subjectNO].reset_index(drop = True).loc[0,z]):
            visit_result.append(z)
                
    return visit_result

# 4) 사용방법
# dict_list = {}
# for i in list(df_batch["USUBJID"].unique()):
#     dict_list[i] = visit_extract(df_batch , "USUBJID", i )
    
# dict_list


# 2) 대상자와 각 대상장의 visit정보를 dict형식으로 묶는다
# ex) {'S32-01002': ['Baseline', 'W08(±7D)', 'W16(±7D)', 'W24(±7D)', 'W32(±7D)'],
#      'S32-01006': ['Baseline', 'W08(±7D)', 'W16(±7D)']}

# 반복문으로 각 여러대상자의 visit 정보를 dict형식을 묶어줌
# dict_list = {}
# for i in list(df_list["Subject No"]):
#     dict_list[i] = visit_extract(df_list , "Subject No", i )

# 3) export data 의 각 대상자의 visit 정보 중 dict_list의 visit정보의 개수가 맞는지 확인하면 끝!
# ex)for i in list(df_list["Subject No"]):
#   print(i, len(df_raw[(df_raw["SubjectNo"] ==i) & (df_raw["Visit"].isin(dict_list[i]))]))


    

#----------------------------------------------------------------
# # Lesion(TRGOC)가 있는데, TRGOC, TRGOCOT가 둘 다 없는 경우
# # Lesion(TRGOC)가 있는데, TRGOC 또는 TRGOCOT가  없는 경우



#kwargs 의 value값은 and, or로 지정, ex) operator = and

def andor(range1, range2, dataframe,*args, **kwargs):
     
    #df_TL에 DM_CMT 컬럼 추가
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")
    
    #col1 = string
    #col2 = string

    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    #kwargs의 key값, value값을 리스트로 받고 인덱싱 한다 -> 나오는 결과괎: ex."TRGMET"
    key = [keys for keys in kwargs.keys()][0]
    value = [values for values in kwargs.values()][0]
    
    #변수가 3개일때
    #operator가 and 일때 , -> TRGOCOT도 없고, TRGOCOSIT도 없는경우
    if len(args)==3:
        if value=="and":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull()) & ( (dataframe[args[1]+"_"+numlist].isnull()) & (dataframe[args[2]+"_"+numlist].isnull()) )]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데, "+args[1]+"_"+numlist+"이 없고,"+args[2]+"_"+numlist+"도 없는 경우"
                df_append = df_append.append(df_empty)
                
        if value=="or":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                df_empty = dataframe[(dataframe[args[0]+"_"+numlist].isnull()) & ( (dataframe[args[1]+"_"+numlist].notnull()) | (dataframe[args[2]+"_"+numlist].notnull()) )]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 NA인데, "+args[1]+"_"+numlist+"이 있거나,"+args[2]+"_"+numlist+"이 있는 경우"
                df_append = df_append.append(df_empty)
    
    
    

    return df_append
    


# # NA, Value_v2

# In[56]:


def valuena(range1, range2, dataframe, *args, **kwargs):
    
    #df_TL에 DM_CMT 컬럼 추가
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")

    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    #kwargs의 key값, value값을 리스트로 받고 인덱싱 한다 -> 나오는 결과괎: ex."TRGMET"
    key = [keys for keys in kwargs.keys()]
    value = [values for values in kwargs.values()]
    
    #TRGOC값이 TRGLD가 없는 경우
    #response 중 NE, CR이 포함된 경우는 제외 , tumor길이는 상관없음
    #valuena(1,6,df_TL,"TRGOC","TRGLD", response="TRGRESP",exclude=["NE","CR"])
    if "response" in key:
        #빈 데이터프레임 생성
        df_empty = pd.DataFrame( columns = new_list)
        df_append = pd.DataFrame( columns = new_list)

        for numlist in list_range:
            df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+"_"+numlist].isnull())]
            df_empty = df_empty[-df_empty[kwargs["response"]].isin(kwargs["exclude"])]
            df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
            df_append = df_append.append(df_empty)
    
    
    #tumor길이에 따라 달라지는 경우, response가 상관없는 경우
    elif "length" in key:
        #튜머길이가 없을 경우        
        if kwargs["length"] == "NA":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)

            for numlist in list_range:
                df_empty = dataframe[dataframe[args[0]+"_"+numlist].notnull()  &  dataframe[args[1]+"_"+numlist].isnull()]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                df_append = df_append.append(df_empty)
                

        
        #튜머길이가 있을 경우
        if kwargs["length"] != "NA":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)

            for numlist in list_range:
                df_empty = dataframe[dataframe[args[0]+"_"+numlist].notnull()  &  dataframe[args[1]+"_"+numlist].isnull()]
                df_empty = df_empty[df_empty[kwargs["length"]+"_"+numlist]!=0]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+"_"+numlist+"가 na인 경우"
                df_append = df_append.append(df_empty)
        
    return df_append





#lenth = tumor 길이
# lenght = "NA" -> 매개변수 기본값 설정 -> 함수에 lenght값을 기입하지 않으면 기본값(여기에서는 NA)값이 기입됨
# length 기입 X -> 매칭이 안됨 -> 기본값 NA를 가지고 있기 때문에 NA로 기입됨 -> tumor길이를 고려하지 않고 함수적용
# length 기입 O -> 매칭        -> 기입한 컬럼으로 기입됨 -> tumor길이가 0이 아닌 경우 query내용 보여줌

def navalue(range1, range2, dataframe, col1, col2, length="NA"):
    
    #df_TL에 DM_CMT 컬럼 추가
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")
    
    #빈 데이터프레임 생성
    df_empty = pd.DataFrame( columns = new_list)
 
    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    if length == "NA":
        #빈 데이터프레임 생성
        df_empty = pd.DataFrame( columns = new_list)
        df_append = pd.DataFrame( columns = new_list)
        for numlist in list_range:
            df_empty = dataframe[dataframe[col1+"_"+numlist].isnull()  &  dataframe[col2+"_"+numlist].notnull()]
            df_empty["DM_CMT"] = col1+"_"+numlist+"가 na이지만,"+col2+numlist+"가 value가 있는 경우"
            df_append = df_append.append(df_empty)
            
    if length != "NA":
        #빈 데이터프레임 생성
        df_empty = pd.DataFrame( columns = new_list)
        df_append = pd.DataFrame( columns = new_list)
        for numlist in list_range:
            df_empty = dataframe[dataframe[col1+"_"+numlist].isnull()  &  dataframe[col2+"_"+numlist].notnull()]
            df_empty = df_empty[df_empty[length+"_"+numlist]!=0]
            df_empty["DM_CMT"] = col1+"_"+numlist+"가 na이지만,"+col2+numlist+"가 value가 있는 경우"
            df_append = df_append.append(df_empty)
             
    return df_append


# # NA, Value TRGDL_SE, TRGDL_IM

# In[9]:


def valuenaseim(range1, range2, dataframe, *args, **kwargs):
    
    #df_TL에 DM_CMT 컬럼 추가
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")

    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    #kwargs의 key값, value값을 리스트로 받고 인덱싱 한다 -> 나오는 결과괎: ex."TRGMET"
    key = [keys for keys in kwargs.keys()]
    value = [values for values in kwargs.values()]
    
    
#col2 가 TRGDL_SE일 때
#length=0, Response가 "NE","CR"이면 제외

    #TRGOC 일때(Target Lesion 일때)
    #valuenaseim(1,2,df_TL, "TRGOC","TRGDL_SE",length = "TRGLDIAM" ,response = "TRGRESP",  exclude =  ["CR","NE"])
    if args[0]=="TRGOC":
        if "SE" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] != "NA":
                if "response" in key:
                    #빈 데이터프레임 생성
                    df_empty = pd.DataFrame( columns = new_list)
                    df_append = pd.DataFrame( columns = new_list)

                    for numlist in list_range:
                        df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                        df_empty = df_empty[df_empty[kwargs["length"]+"_"+numlist]!=0]
                        df_empty = df_empty[-df_empty[kwargs["response"]].isin(kwargs["exclude"])]
                        df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                        df_append = df_append.append(df_empty)

            # length가 NA인 경우는 없을것으로 판단하여 주석처리
            # if kwargs["length"] == "NA":
            #     if "response" in key:
            #         #빈 데이터프레임 생성
            #         df_empty = pd.DataFrame( columns = new_list)
            #         df_append = pd.DataFrame( columns = new_list)

            #         for numlist in list_range:
            #             df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
            #             df_empty = df_empty[-df_empty[kwargs["response"]].isin(kwargs["exclude"])]
            #             df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
            #             df_append = df_append.append(df_empty)


        #valuenaseim(1,2,df_TL, "TRGOC","TRGDL_IM",length = "TRGLDIAM" ,response = "TRGRESP",  exclude =  ["CR","NE"])
        #col2 가 TRGDL_IM일 때
        if "IM" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] != "NA":
                if "response" in key:
                    #빈 데이터프레임 생성
                    df_empty = pd.DataFrame( columns = new_list)
                    df_append = pd.DataFrame( columns = new_list)

                    for numlist in list_range:
                        df_empty = dataframe[dataframe[args[0]+"_"+numlist].notnull()  &  dataframe[args[1]+numlist].isnull()]
                        df_empty = df_empty[df_empty[kwargs["length"]+"_"+numlist]!=0]
                        df_empty = df_empty[-df_empty[kwargs["response"]].isin(kwargs["exclude"])]
                        df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                        df_append = df_append.append(df_empty)

            if kwargs["length"] == "NA":
                if "response" in key:
                    #빈 데이터프레임 생성
                    df_empty = pd.DataFrame( columns = new_list)
                    df_append = pd.DataFrame( columns = new_list)

                    for numlist in list_range:
                        df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                        df_empty = df_empty[-df_empty[kwargs["response"]].isin(kwargs["exclude"])]
                        df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                        df_append = df_append.append(df_empty)
    
    #NTRGOC 일때(Non Target Lesion 일때)
    if args[0]=="NTRGOC":
        if "SE" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] == "NA":
                if "response" in key:
                    #빈 데이터프레임 생성
                    df_empty = pd.DataFrame( columns = new_list)
                    df_append = pd.DataFrame( columns = new_list)

                    for numlist in list_range:
                        df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                        df_empty = df_empty[-df_empty[kwargs["response"]+"_"+numlist].isin(kwargs["exclude"])]
                        df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                        df_append = df_append.append(df_empty)


        #col2 가 TRGDL_IM일 때
        if "IM" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] == "NA":
                if "response" in key:
                    #빈 데이터프레임 생성
                    df_empty = pd.DataFrame( columns = new_list)
                    df_append = pd.DataFrame( columns = new_list)

                    for numlist in list_range:
                        df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                        df_empty = df_empty[-df_empty[kwargs["response"]+"_"+numlist].isin(kwargs["exclude"])]
                        df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                        df_append = df_append.append(df_empty)
        
    #NTRGOC 일때(Non Target Lesion 일때)
    if args[0]=="NEWLOC":
        if "SE" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] == "NA":
                #빈 데이터프레임 생성
                df_empty = pd.DataFrame( columns = new_list)
                df_append = pd.DataFrame( columns = new_list)

                for numlist in list_range:
                    df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                    df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                    df_append = df_append.append(df_empty)


        #col2 가 TRGDL_IM일 때
        if "IM" in args[1].split("_"):
            #튜머길이가 있을 경우, 
            #Response가 CR 또는 NE일경우 제외
            if kwargs["length"] == "NA":
                #빈 데이터프레임 생성
                df_empty = pd.DataFrame( columns = new_list)
                df_append = pd.DataFrame( columns = new_list)

                for numlist in list_range:
                    df_empty = dataframe[(dataframe[args[0]+"_"+numlist].notnull())  &  (dataframe[args[1]+numlist].isnull())]
                    df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 value가 있는데,"+args[1]+numlist+"가 na인 경우"
                    df_append = df_append.append(df_empty)
   
    return df_append


# # Other, Na, value

# In[8]:


#TRGMET 값이 Other인데 , TRGMETOT_n 이 없는 경우(TRGLD_n이 0이 아닌경우)

def otherna(range1, range2, dataframe,*args, **kwargs):
    
    #df_TL에 DM_CMT 컬럼 추가(df_TL에는 DM_CMT컬럼이 없기 때문에)
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")    
    
    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    #kwargs의 key값, value값을 리스트로 받고 인덱싱 한다 -> 나오는 결과괎: ex."TRGMET"
    key = [keys for keys in kwargs.keys()][0]
    value = [values for values in kwargs.values()][0]
    
    
    #변수가 3개일때
    #tumor길이가 필요없을 때, 일반적인 상황 : if value=="NA" ->default값
    #ex) otherna(1,6,df_TL,"TRGOC","TRGOCOT","TRGOCSITE",length="NA")
    if len(args)==3:
        if value=="NA":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                df_empty = dataframe[(dataframe[args[0]+"_"+numlist].isin(["OTHER" , "Other","Others"])) & ( (dataframe[args[1]+"_"+numlist].isnull()) & (dataframe[args[2]+"_"+numlist].isnull()) )]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"가 Other인데 "+args[1]+"_"+numlist+"이 없고,"+args[2]+"_"+numlist+"도 없는 경우"
                df_append = df_append.append(df_empty)
                
                
    #변수가 2개일때
    #tumor길이가 필요할 때, 특수한 상황 : if value!="NA" ->tumor길이가 0이 아닌 경우
    #ex) otherna(1,6,df_TL,"TRGMET","TRGMETOT",length="TRGLD")
    if len(args)==2:
        if value!="NA":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                #결과가 출력될 dataframe = df_NA : TRGOCSITE_1_NA
                df_empty = dataframe[(dataframe[args[0]+"_"+numlist].isin(["OTHER", "Other","Others"]))  & ( dataframe[args[1]+"_"+numlist].isnull() )]

                #value값(tumor길이)가 0인것은 제외 
                df_empty = df_empty[df_empty[value+"_"+numlist]!=0]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"값이 Other인데,"+args[1]+numlist+"가 없는 경우"
                df_append = df_append.append(df_empty)
                
        if value=="NA":
            #빈 데이터프레임 생성
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                #결과가 출력될 dataframe = df_NA : TRGOCSITE_1_NA
                df_empty = dataframe[(dataframe[args[0]+"_"+numlist].isin(["OTHER" , "Other","Others"]))  & ( dataframe[args[1]+"_"+numlist].isnull() )]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"값이 Other인데,"+args[1]+numlist+"가 없는 경우"
                df_append = df_append.append(df_empty)
    
    
    #최종 데이터프레임 산출
    return df_append



#Other가 아닌데, 값이 있는 경우(TRGOC값이 Others가 아닌데, TRGOCOT 이 있는 경우)
# ex)nothervalue(1,6,df_TL , "TRGOC","TRGOCOT" , length = "NA")
def nothervalue(range1, range2, dataframe,*args, **kwargs):
    
    #df_TL에 DM_CMT 컬럼 추가(df_TL에는 DM_CMT컬럼이 없기 때문에)
    new_list = list(dataframe.columns)
    new_list.append("DM_CMT")
    
    #범위 지정->string으로 받는다
    list_range = [str(i) for i in list(range(range1, range2))]
    
    #kwargs의 key값, value값을 리스트로 받고 인덱싱 한다 -> 나오는 결과괎: ex."TRGMET"
    key = [keys for keys in kwargs.keys()][0]
    value = [values for values in kwargs.values()][0]
                      
    #변수가 2개일때
        #tumor길이가 필요할 때, 일반적인 상황 : if value!="NA":
    if len(args)==2:
        if value=="NA":
            df_empty = pd.DataFrame( columns = new_list)
            df_append = pd.DataFrame( columns = new_list)
            for numlist in list_range:
                df_empty = dataframe[(-dataframe[args[0]+"_"+numlist].isin(["OTHER" , "Other","Others"]))  & ( dataframe[args[1]+"_"+numlist].notnull() )]
                df_empty["DM_CMT"] = args[0]+"_"+numlist+"값이 Other가 아닌데,"+args[1]+numlist+"가 있는 경우"
                df_append = df_append.append(df_empty)
    
    #최종 데이터프레임 산출
    return df_append



#TRGRESP 판별 알고리즘
# nadirper = nadir % 나타내는 컬럼
# baselineper = baseline % 나타내는 컬럼
def TargetResponse(dataframe , nadirper , baselineper):
    #dataframe index 재정렬
    dataframe = dataframe.reset_index(drop=True)
    
    #index순으로 반복하여 TRGRESP산출
    for i in list(range(len(dataframe))):
        
        #PCNSLD가 20%보다 크고, 차이가 5보다 크면, PD
        if dataframe.loc[i,nadirper]>=20:
            if dataframe.loc[i,"ABS"]>=5:
                dataframe.loc[i,"TRGRESP_YJW"]="PD"
            
            #만약 차이가 5보다 작다면, SD
            elif dataframe.loc[i,"ABS"]<5:
                dataframe.loc[i,"TRGRESP_YJW"]="SD"
            
        elif -100<dataframe.loc[i,baselineper]<=-30:
            dataframe.loc[i,"TRGRESP_YJW"]="PR"
            
        elif dataframe.loc[i,baselineper]<=-100:
            dataframe.loc[i,"TRGRESP_YJW"]="CR"
            
        else:
            dataframe.loc[i,"TRGRESP_YJW"]="SD"
            
            
    #VISIT 이 screening 이면 TRGRESP 값이 NA 이다.
    dataframe["TRGRESP_YJW"][dataframe["VISIT"].isin(["Baseline","BL" , "Screening"])]=np.nan
    
    return dataframe



def TargetResponse_YN(dataframe , TargetResponsecol):
    
    #판독자와 알고리즘 결과값이 다른 경우 표시       
    for i in list(range(len(dataframe))):
        if dataframe.loc[i, TargetResponsecol] != dataframe.loc[i, "TRGRESP_YJW"]:
            dataframe.loc[i,"YN"] = "N"
            
        if (pd.isnull(dataframe.loc[i, TargetResponsecol])) & (pd.isnull(dataframe.loc[i, "TRGRESP_YJW"])):
            dataframe.loc[i,"YN"] = "Y"
            


        if dataframe.loc[i, TargetResponsecol] == dataframe.loc[i, "TRGRESP_YJW"]:
            dataframe.loc[i,"YN"] = "Y"
                
    return dataframe



#------------------------------------------
# Overall Response logic

def OverallResponse(dataframe ,TRGIND, TRGRESP , NTRGRESP , NEWLIND ):
    for i in list(range(len(dataframe))):
        if dataframe.loc[i,TRGIND]=="Yes":                    
            if dataframe.loc[i,TRGRESP]=="PD":
                dataframe.loc[i,"OVRESP_YJW"]="PD"
            
            elif dataframe.loc[i,NTRGRESP]=="PD":
                dataframe.loc[i,"OVRESP_YJW"]="PD"
                
            elif dataframe.loc[i,NEWLIND]=="Yes":
                dataframe.loc[i,"OVRESP_YJW"]="PD"
                
                
            elif dataframe.loc[i,TRGRESP]=="CR":
                if dataframe.loc[i,NTRGRESP]=="CR":
                    if dataframe.loc[i,NEWLIND]=="No":
                        dataframe.loc[i,"OVRESP_YJW"]="CR"
                        
                elif dataframe.loc[i,NTRGRESP] in ["CR","Non-CR/Non-PD","Not evaluable","NE"]:
                    if dataframe.loc[i,NEWLIND]=="No":
                        dataframe.loc[i,"OVRESP_YJW"]="PR"
                        
            elif dataframe.loc[i,TRGRESP]=="PR":
                if dataframe.loc[i,NTRGRESP] in ["CR","Non-CR/Non-PD","Not evaluable","NE"]:
                    if dataframe.loc[i,NEWLIND]=="No":
                        dataframe.loc[i,"OVRESP_YJW"]="PR"
                        
            elif dataframe.loc[i,TRGRESP]=="SD":
                if dataframe.loc[i,NTRGRESP] in ["CR","Non-CR/Non-PD","Not evaluable","NE"]:
                        if dataframe.loc[i,NEWLIND]=="No":
                            dataframe.loc[i,"OVRESP_YJW"]="SD"
                        
            elif dataframe.loc[i,TRGRESP] in ["Not Evaluable","NE"]:
                if dataframe.loc[i,NTRGRESP] == "Non-CR/Non-PD":
                    if dataframe.loc[i,NEWLIND]=="No":
                        dataframe.loc[i,"OVRESP_YJW"]="NE"
                    
        elif dataframe.loc[i,TRGIND]=="No":
            if dataframe.loc[i,NTRGRESP]=="CR":
                if dataframe.loc[i,NEWLIND]=="No":
                    dataframe.loc[i,"OVRESP_YJW"]="CR"
                    
            elif dataframe.loc[i,NTRGRESP]=="Non-CR/Non-PD":
                if dataframe.loc[i,NEWLIND]=="No":
                    dataframe.loc[i,"OVRESP_YJW"]="non-CR/non-PD"
                    
            elif dataframe.loc[i,NTRGRESP] in ["Not evaluable","NE"]:
                if dataframe.loc[i,NEWLIND]=="No":
                    dataframe.loc[i,"OVRESP_YJW"]="NE"
                    
            elif dataframe.loc[i,NTRGRESP]=="PD":
                dataframe.loc[i,"OVRESP_YJW"]="PD"
                
            if dataframe.loc[i,NEWLIND]=="Yes":
                dataframe.loc[i,"OVRESP_YJW"]="PD"
        

        else:
            dataframe.loc[i,"OVRESP_YJW"]=np.nan
        
    return dataframe


def OverallResponse_YN(dataframe , OverallResponsecol):
    
    #판독자와 알고리즘 결과값이 다른 경우 표시       
    for i in list(range(len(dataframe))):
        if dataframe.loc[i, OverallResponsecol] != dataframe.loc[i, "OVRESP_YJW"]:
            dataframe.loc[i,"YN"] = "N"
            
        if (pd.isnull(dataframe.loc[i, OverallResponsecol])) & (pd.isnull(dataframe.loc[i, "OVRESP_YJW"])):
            dataframe.loc[i,"YN"] = "Y"
            


        if dataframe.loc[i, OverallResponsecol] == dataframe.loc[i, "OVRESP_YJW"]:
            dataframe.loc[i,"YN"] = "Y"
                
    return dataframe
        



# Modality와 Scan Type에 따라 Date가 잘 입력 되었는가  ( Incorrect Check )         2022-10-23
# ex) CT SCAN , chest 이면 영상촬영일자의 CT-Chest Date와 동일 및 데이터를 가져와야한다.


def ScanDataCheck(dataframe):
    result_dataframe = pd.dataframe(coloums=dataframe.columns)
    result_dataframe['DM_CMT']=np.nan
    # TUMETHOD_NT_i : CT,MRI,Other  , TUIMG_NT_i : Chest,Abdomen/Pelvis,Other , TUDTC_NT_i , 
    for i in range(len(dataframe)):
        for j in range(1,6):
            modality = "TUMETHOD_NT_"+str(j)
            scan_type = "TUIMG_NT_"+str(j)
            scan_date = "TUDTC_NT_"+str(j)
            if (dataframe.loc[i,modality]!=None and dataframe.loc[i,scan_type]!=None):
                if dataframe.loc[i,scan_date] == None:
                    new_line=dataframe.loc[i,:]
                    new_line["DM_CMT"] = "Scan Type 날짜를 불러오지 못한 경우 Non-Target Lession {}번째".format(j)
                    result_dataframe.append(new_line)
                # 아래는 옵션을 잘못 선택하여 당연히 없는 경우
                else:
                    original_type = "TUDTC_"
                    if not dataframe.loc[i,modality] in ["CT","MRI"]:
                        original_type+="OT_OT"
                    else:
                        if dataframe.loc[i,modality]=="CT_":
                            original_type+="CT"
                        else:
                            original_type+="MRI_"

                        if dataframe.loc[i,scan_type]=="Chest":
                            original_type+="CHEST"
                        elif dataframe.loc[i,scan_type]=="Abdomen/Pelvis":
                            original_type+="ABD"
                        else:
                            original_type+="OT"
                    
                    if dataframe.loc[i,original_type]==None:
                        new_line=dataframe.loc[i,:]
                        new_line["DM_CMT"] = "옵션을 잘못 선택해서 날짜 값이 없는 타입을 선택한 경우 Non-Target Lession {}번째".format(j)
                        result_dataframe.append(new_line)
                
    return result_dataframe      




# Date of Target , NonTarget , Date of image acquisition 가 Logic에 따라 입력이 잘 되었는가     2022-10-25
# ex) PD는 가장 최근 날짜 그외 나머지는 가장 과거 날짜가 제대로 기재되어있는지 검증하는 코드 

def checkData(dataframe):
    targetLesion = ['TUDTC_T_1','TUDTC_T_2','TUDTC_T_3','TUDTC_T_4','TUDTC_T_5'] # TRGRESP_RS /RSDTC_T         해당 컬럼 값은 Gen001-101 기준 
    nonTargetLesion = ['TUDTC_NT_1','TUDTC_NT_2','TUDTC_NT_3','TUDTC_NT_4','TUDTC_NT_5'] # NTRGRESP_RS / RSDTC_NT
    newLesion = ['TUIMNO_NEW_1','TUIMNO_NEW_2','TUIMNO_NEW_3','TUIMNO_NEW_4','TUIMNO_NEW_5'] # OVRLRESP_RS / RSDTC_RS
    
    result_df = pd.DataFrame(columns=dataframe.columns)
    result_df["DM_CMT"]=np.nan

    for i in range(len(dataframe)):
        # PD 가장 과거 / 나머지는 최근 날짜
        targetDate = [dataframe.loc[i,x] for x in targetLesion if dataframe.loc[i,x]!=None]
        # ===== ↑1 코드는 ↓4줄의 코드와 같다.
        # targetDate=[]
        # for x in targetLesion:
        #   if dataframe.loc[i,x]!=None:
        #     targetDate.append(dataframe.loc[i,x])

        def pd_Message(Message):
            new_line=dataframe.loc[i,:]
            new_line["DM_CMT"]= Message
            result_df.append(new_line)


        targetDate.sort()     # sort로 정렬한 뒤 가장 과거 인덱스 0   가장 최근 인덱스 -1
        if dataframe.loc[i,"TRGRESP_RS"]=="PD" and dataframe.loc[i,'RSDTC_T']!=targetDate[0]:
        #   new_line=dataframe.loc[i,:]
        #   new_line["DM_CMT"]= "targetLesion 이 PD 인데 날짜가 가장 과거가 아님"
        #   result_df.append(new_line)
            pd_Message("TargetLesion이 PD 인데, 날짜가 가장 과거가 아님")
            
        elif dataframe.loc[i,"TRGRESP_RS"]!="PD" and dataframe.loc[i,'RSDTC_T']!=targetDate[-1]:
            pd_Message("TargetLesion이 PD가 아닌데, 날짜가 가장 최근이 아님")

        nonTargetDate= [dataframe.loc[i,x] for x in nonTargetLesion if dataframe.loc[i,x]!=None]
        nonTargetDate.sort()

        if dataframe.loc[i,"NTRGRESP_RS"]=="PD" and dataframe.loc[i,'RSDTC_NT']!=targetDate[0]:
            pd_Message("NonTargetLesion이 PD 인데, 날짜가 가장 과거가 아님")
            
        elif dataframe.loc[i,"NTRGRESP_RS"]!="PD" and dataframe.loc[i,'RSDTC_NT']!=targetDate[-1]:
            pd_Message("NonTargetLesion이 PD가 아닌데, 날짜가 가장 최근이 아님")

        newLesionDate=[dataframe.loc[i,x] for x in newLesion if dataframe.loc[i,x]!=None]
        overAllDate=newLesionDate+nonTargetDate+targetDate
        overAllDate.sort()

        if dataframe.loc[i,"OVRLRESP_RS"]=="PD" and dataframe.loc[i,'RSDTC_RS']!=targetDate[0]:
            pd_Message("Overall이 PD 인데, 날짜가 가장 과거가 아님")
            
        elif dataframe.loc[i,"OVRLRESP_RS"]!="PD" and dataframe.loc[i,'RSDTC_RS']!=targetDate[-1]:
            pd_Message("Overall이 PD가 아닌데, 날짜가 가장 최근이 아님")
      
    return result_df


