
// AiCRO 기준 Setting의 DVS에서 사용할 수 있으며, 적용하고자 할 때 OID값을 확인하여야 한다.



// 입력 날짜가 YYYY-MM-DD 형식이 아니면 메세지 출력  2022-10-25
// Date기능을 사용할 OID값 마다 각각 따로 사용하여야 한다.  즉, DTF 내 Date 기능이 3개라면 OID값을 변경하여 3번 사용 
var message =""; 
var trueFalse = false;

date=ITEM.getValue("DTF_SCANDTC_CT")  

const date_Check = /\d{4}-\d{2}-\d{2}/;  // 정규표현식
if((ITEM.getValue("DTF_SCANDTC_CT") === null) && megic.isNull(ITEM.getValue("DTF_SCANDTC_CT"))) {
    var message = "날짜 미기재";
    
    trueFalse = true;
    var mandatory = false;
    
    ITEM.alarm("prompt",trueFalse,message,mandatory,"DTF_SCANDTC_CT")
}else if (date !== null && !date_Check.test(date)){
    console.log(date_Check.test(date))
    var message = "YYYY-MM-DD 형식이 아닙니다.";
    trueFalse = true;
    var mandatory = false;
    
    ITEM.alarm("prompt",trueFalse,message,mandatory,"DTF_SCANDTC_CT");
}else{
    // 조건 만족시 경고메세지 삭제
    ITEM.alarm("prompt",trueFalse,message,mandatory,"DTF_SCANDTC_CT");
}





// Indicator NO -> All Change Null  2022-10-20
// Lesion Indicator를 No로 클릭하면, No.1 ~ No.5 안의 밸류 값들이 일체히 null값으로 변경
if(ITEM.getValue("R_NEWLIND")!=="Yes") {    // Lesion Indicator의 OID값 확인하기
    let resetList=["R_NEWLOC_","R_NEWLOCOT_","R_NEWLOCSITE_","R_NEWLOCSITE_MUL_","R_NEWLDL_SE","R_NEWLDL_IM","R_NEWLMET_","R_NEWLMETOT_","R_NLIMG_","R_NLDTC_","R_NEWCMT_"];
    for (let i=1;i<6;i++){
        for (const resetItem of resetList){
            ITEM.setValue(null,resetItem+i);
        }
    }
    // ITEM.setValue(null,"");
}


// // Indicator NO -> All Change Null 검증하는 코드
// else{
//     let resetList=["R_NEWLOC_","R_NEWLOCOT_","R_NEWLOCSITE_","R_NEWLOCSITE_MUL_","R_NEWLDL_SE","R_NEWLDL_IM","R_NEWLMET_","R_NEWLMETOT_","R_NLIMG_","R_NLDTC_","R_NEWCMT_"];
//     for (let i=1;i<6;i++){
//         for (const resetItem of resetList){
//             let x=ITEM.getValue(resetItem+i);
//                 if (x !==null){
//             console.log(resetItem+i+" : "+x);
//                 }
//         }
//     }
// }




