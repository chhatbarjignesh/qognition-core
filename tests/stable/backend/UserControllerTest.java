package com.qognition;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class UserControllerTest {

    @BeforeAll
    public static void setup() {
        RestAssured.baseURI = "http://localhost:8080";
    }

    @Test
    public void getAllUsers_ReturnsListWithInitialData() {
        given()
        .when()
            .get("/users")
        .then()
            .statusCode(200)
            .contentType(ContentType.JSON)
            .body("$", hasSize(3))
            .body("name", hasItems("Alice Smith", "Bob Jones", "Carol White"))
            .body("email", hasItems("alice@qognition.io", "bob@qognition.io", "carol@qognition.io"));
    }

    @Test
    public void getUserById_WhenUserExists_ReturnsUserObject() {
        given()
            .pathParam("id", 1)
        .when()
            .get("/users/{id}")
        .then()
            .statusCode(200)
            .body("id", equalTo(1))
            .body("name", equalTo("Alice Smith"))
            .body("role", equalTo("admin"));
    }

    @Test
    public void getUserById_WhenUserDoesNotExist_Returns404NotFound() {
        given()
            .pathParam("id", 999)
        .when()
            .get("/users/{id}")
        .then()
            .statusCode(404);
    }

    @Test
    public void getUsersByRole_WhenRoleExists_ReturnsFilteredList() {
        given()
            .pathParam("role", "viewer")
        .when()
            .get("/users/role/{role}")
        .then()
            .statusCode(200)
            .body("$", hasSize(1))
            .body("[0].name", equalTo("Bob Jones"))
            .body("[0].role", equalTo("viewer"));
    }

    @Test
    public void getUsersByRole_ShouldBeCaseInsensitive() {
        given()
            .pathParam("role", "EDITOR")
        .when()
            .get("/users/role/{role}")
        .then()
            .statusCode(200)
            .body("$", hasSize(1))
            .body("[0].name", equalTo("Carol White"))
            .body("[0].role", equalTo("editor"));
    }

    @Test
    public void getUsersByRole_WhenNoMatches_ReturnsEmptyList() {
        given()
            .pathParam("role", "nonexistent")
        .when()
            .get("/users/role/{role}")
        .then()
            .statusCode(200)
            .body("$", hasSize(0));
    }
}