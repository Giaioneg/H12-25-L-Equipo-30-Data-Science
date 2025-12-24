package com.hackathon.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class FlightDataDTO {

    @JsonProperty("MONTH")
    private Integer MONTH;

    @JsonProperty("DAY_OF_WEEK")
    private Integer DAY_OF_WEEK;

    @JsonProperty("DISTANCE_GROUP")
    private Integer DISTANCE_GROUP;

    @JsonProperty("SEGMENT_NUMBER")
    private Integer SEGMENT_NUMBER;

    @JsonProperty("CONCURRENT_FLIGHTS")
    private Integer CONCURRENT_FLIGHTS;

    @JsonProperty("PRCP")
    private Double PRCP;

    @JsonProperty("TMAX")
    private Double TMAX;

    @JsonProperty("AWND")
    private Double AWND;

    @JsonProperty("PLANE_AGE")
    private Integer PLANE_AGE;

    @JsonProperty("AIRPORT_FLIGHTS_MONTH")
    private Integer AIRPORT_FLIGHTS_MONTH;

    @JsonProperty("CARRIER_NAME")
    private String CARRIER_NAME;

    @JsonProperty("DEPARTING_AIRPORT")
    private String DEPARTING_AIRPORT;

    @JsonProperty("DEP_TIME_BLK")
    private String DEP_TIME_BLK;

}