package com.qognition;

import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

public class QognitionApiPropertiesTest {

    @BeforeAll
    public static void setup() {
        RestAssured.baseURI = "http://localhost:8080";
    }

    @Test
    @DisplayName("Happy Path: Verify actuator health endpoint returns UP status")
    public void testActuatorHealth() {
        given()
            .when()
            .get("/actuator/health")
            .then()
            .statusCode(200)
            .body("status", equalTo("UP"));
    }

    @Test
    @DisplayName("Happy Path: Verify dashboard summary returns expected structure")
    public void testDashboardSummary() {
        given()
            .accept(ContentType.JSON)
            .when()
            .get("/dashboard/summary")
            .then()
            .statusCode(200)
            .contentType(ContentType.JSON)
            .body("status",  equalTo("ok"))
            .body("total",   notNullValue())
            .body("message", notNullValue());
    }

    @Test
    @DisplayName("Happy Path: Verify pagination endpoint returns default page structure")
    public void testPagination() {
        given()
            .accept(ContentType.JSON)
            .when()
            .get("/pagination")
            .then()
            .statusCode(200)
            .contentType(ContentType.JSON)
            .body("page",  equalTo(0))
            .body("size",  equalTo(10))
            .body("total", notNullValue());
    }

    @Test
    @DisplayName("Negative Test: Verify unknown endpoints return 404")
    public void testUnknownEndpoint() {
        given()
            .when()
            .get("/unknown-endpoint-xyz")
            .then()
            .statusCode(404);
    }
}
