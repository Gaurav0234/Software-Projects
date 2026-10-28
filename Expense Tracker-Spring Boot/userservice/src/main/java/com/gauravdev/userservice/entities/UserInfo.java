package com.gauravdev.userservice.entities;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserInfo {

    @Id
    private String userId;

    private String firstName;
    private String lastName;
    private Long phoneNumber;
    private String email;
    private String profilePic;
}
