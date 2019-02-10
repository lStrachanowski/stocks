if(document.getElementById('download')){
    document.getElementById('download').addEventListener('click', ()=>{
        document.getElementsByClassName('loader')[0].style.display = 'block';
        const request = new XMLHttpRequest();
        request.open('POST', '/download');
        request.onreadystatechange = () =>{
            if(request.readyState === 4 && request.status === 200){
                document.getElementsByClassName('loader')[0].style.display = 'none';
            }
        }
        request.send();
    
    });
}


if(document.getElementById('analyze')){
    document.getElementById('analyze').addEventListener('click', ()=>{
        document.getElementsByClassName('loader')[0].style.display = 'block';
    });
}


    
