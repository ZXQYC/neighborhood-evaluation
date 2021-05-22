let map;

function convertPt(pt) {
    /* Convert a point (in the form [longitude, latitude]) into an object usable by Google Maps */
    return {lat: pt[1], lng: pt[0]};
}

function displayMarkers(objs) {
    /* Displays a list of markers on the map.
    Input: An array of the form [{point: [x,y], label: 'something'}, ...] */
    objs.forEach(obj => {
        new google.maps.Marker({
            position: convertPt(obj.point),
            label: obj.label,
            map: map,
        });
    });
}

function initMap() {
    /*
    Creates the map!
    */
    // get the point the map should be centered
    const house_cent = [(house1_loc[0]+house2_loc[0])/2, (house1_loc[1]+house2_loc[1])/2];
    // create map
    map = new google.maps.Map(document.getElementById("zmap"), {
        center: convertPt(house_cent),
        zoom: 14,
    });
    // create markers
    const marks = [
        {point: house1_loc, label: '1'},
        {point: house2_loc, label: '2'}
    ];
    displayMarkers(marks);
}