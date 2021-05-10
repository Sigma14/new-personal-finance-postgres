/**
 * App Calendar Events
 */


function showCalenders(event_data)
{
    'use strict';
    var date = new Date();
    var nextDay = new Date(new Date().getTime() + 24 * 60 * 60 * 1000);
    // prettier-ignore
    var nextMonth = date.getMonth() === 11 ? new Date(date.getFullYear() + 1, 0, 1) : new Date(date.getFullYear(), date.getMonth() + 1, 1);
    // prettier-ignore
    var prevMonth = date.getMonth() === 11 ? new Date(date.getFullYear() - 1, 0, 1) : new Date(date.getFullYear(), date.getMonth() - 1, 1);

    var calender_data = []; // create an empty array

    for (let i = 0; i < event_data.length; i++)
    {
        var date_event = new Date(event_data[i]['date']);
        var nextDay = new Date(date_event.getTime() + 24 * 60 * 60 * 1000);
        calender_data.push({
                                id: i + 1,
                                url: '/bill_detail/' + event_data[i]['label_id'],
                                title: event_data[i]['label'],
                                start: date_event,
                                end: nextDay ,
                                allDay: true,
                                extendedProps: {
                                  calendar: event_data[i]['calendar_type']
                                }
                           });

    }
    console.log(calender_data);
    events = calender_data
}

var events = events
console.log(events);