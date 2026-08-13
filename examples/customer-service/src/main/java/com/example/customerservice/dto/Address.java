package com.example.customerservice.dto;

import jakarta.validation.constraints.NotBlank;

public class Address {

    @NotBlank
    private String city;

    private String postalCode;

    public String getCity() {
        return city;
    }

    public void setCity(String city) {
        this.city = city;
    }

    public String getPostalCode() {
        return postalCode;
    }

    public void setPostalCode(String postalCode) {
        this.postalCode = postalCode;
    }
}
