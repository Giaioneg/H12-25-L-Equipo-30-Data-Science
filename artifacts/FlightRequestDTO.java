package com.hackathon.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class FlightRequestDTO {

    @JsonProperty("CARRIER_NAME")
    private String CARRIER_NAME;

    @JsonProperty("DEPARTING_AIRPORT")
    private String DEPARTING_AIRPORT;

    @JsonProperty("FECHA")
    private String FECHA;

    @JsonProperty("HORA")
    private String HORA;

    @JsonProperty("PRCP")
    private String PRCP;

    @JsonProperty("SNOW")
    private String SNOW;

    @JsonProperty("AWND")
    private String AWND;

}