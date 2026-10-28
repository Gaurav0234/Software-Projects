package org.example.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.*;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class UserInfoDto {

    @NonNull
    private String username;
    @NonNull
    private String password;
    @NonNull
    private String firstName; //first_name
    @NonNull
    private String lastName; //last_name
    @NonNull
    private Long phoneNumber;
    @NonNull
    private String email;
}