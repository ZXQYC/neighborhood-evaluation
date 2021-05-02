let map;

function convertPt(pt) {
    return {lat: pt[1], lng: pt[0]};
}

function displayMarkers(objs) {
    objs.forEach(obj => {
        new google.maps.Marker({
            position: convertPt(obj.point),
            label: obj.label,
            map: map,
        });
    });
}

function initMap() {
    const house_cent = [(house1_loc[0]+house2_loc[0])/2, (house1_loc[1]+house2_loc[1])/2];
    map = new google.maps.Map(document.getElementById("zmap"), {
        center: convertPt(house_cent),
        zoom: 14,
    });
    const marks = [
        {point: house1_loc, label: '1'},
        {point: house2_loc, label: '2'}
    ];
    console.log(marks);
    displayMarkers(marks);
}