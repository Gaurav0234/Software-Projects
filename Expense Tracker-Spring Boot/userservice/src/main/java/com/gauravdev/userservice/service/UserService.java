package com.gauravdev.userservice.service;

import com.gauravdev.userservice.entities.UserInfo;
import com.gauravdev.userservice.entities.UserInfoDto;
import com.gauravdev.userservice.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserRepository userRepository;

    public UserInfoDto createOrUpdateUser(UserInfoDto userInfoDto) {
        Optional<UserInfo> existingUserInfoOptional = userRepository.findByUserId(userInfoDto.getUserId());

        UserInfo userInfoToSave;
        if (existingUserInfoOptional.isPresent()) {
            // Update existing user
            userInfoToSave = existingUserInfoOptional.get();
            userInfoToSave.setFirstName(userInfoDto.getFirstName());
            userInfoToSave.setLastName(userInfoDto.getLastName());
            userInfoToSave.setPhoneNumber(userInfoDto.getPhoneNumber());
            userInfoToSave.setEmail(userInfoDto.getEmail());
            userInfoToSave.setProfilePic(userInfoDto.getProfilePic());
        } else {
            // Create new user
            userInfoToSave = userInfoDto.transformToUserInfo();
        }
        UserInfo savedUserInfo = userRepository.save(userInfoToSave);
        return new UserInfoDto(savedUserInfo);
    }

    public UserInfoDto getUser(String userId) throws Exception {
        Optional<UserInfo> userInfoOptional = userRepository.findByUserId(userId);
        if (userInfoOptional.isEmpty()) {
            throw new Exception("User not found");
        }
        return new UserInfoDto(userInfoOptional.get());
    }

    public UserInfoDto getUser(UserInfoDto userInfoDto) throws Exception{
        Optional<UserInfo> userInfoOptional = userRepository.findByUserId(userInfoDto.getUserId());
        if(userInfoOptional.isEmpty()){
            throw new Exception("user not found");
        }

        UserInfo userInfo = userInfoOptional.get();
        return new UserInfoDto(
                userInfo.getUserId(),
                userInfo.getFirstName(),
                userInfo.getLastName(),
                userInfo.getPhoneNumber(),
                userInfo.getEmail(),
                userInfo.getProfilePic()

        );
    }
}
