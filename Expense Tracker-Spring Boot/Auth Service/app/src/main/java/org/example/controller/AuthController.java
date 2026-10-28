package org.example.controller;

import lombok.AllArgsConstructor;
import org.example.entities.RefreshToken;
import org.example.eventProducer.UserInfoEvent;
import org.example.eventProducer.UserInfoProducer;
import org.example.model.UserInfoDto;
import org.example.response.JwtResponseDTO;
import org.example.service.JwtService;
import org.example.service.RefreshTokenService;
import org.example.service.UserDetailsServiceImpl;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Objects;

@AllArgsConstructor
@RestController
public class AuthController
{

    private final JwtService jwtService;
    private final RefreshTokenService refreshTokenService;
    private final UserDetailsServiceImpl userDetailsService;
    private final UserInfoProducer userInfoProducer;

    @PostMapping("auth/v1/signup")
    public ResponseEntity<JwtResponseDTO> SignUp(@RequestBody UserInfoDto userInfoDto) {
        try {

            String userId = userDetailsService.signupUser(userInfoDto);

            if (Objects.isNull(userId)) {
                return new ResponseEntity<>(null, HttpStatus.BAD_REQUEST);
            }

            UserInfoEvent event = UserInfoEvent.builder()
                    .firstName(userInfoDto.getFirstName())
                    .lastName(userInfoDto.getLastName())
                    .email(userInfoDto.getEmail())
                    .phoneNumber(userInfoDto.getPhoneNumber())
                    .userId(userId)
                    .build();

            userInfoProducer.sendEventToKafka(event);

            RefreshToken refreshToken =
                    refreshTokenService.createRefreshToken(userInfoDto.getUsername());

            String jwtToken =
                    jwtService.GenerateToken(userInfoDto.getUsername());

            JwtResponseDTO response = JwtResponseDTO.builder()
                    .accessToken(jwtToken)
                    .token(refreshToken.getToken())
                    .userId(userId)
                    .build();

            return new ResponseEntity<>(response, HttpStatus.OK);

        } catch (Exception ex) {
            ex.printStackTrace();
            return new ResponseEntity<>(null, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}
