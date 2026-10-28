package com.gauravdev.userservice.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gauravdev.userservice.entities.UserInfo;
import com.gauravdev.userservice.entities.UserInfoDto;
import com.gauravdev.userservice.repository.UserRepository;
import com.gauravdev.userservice.service.UserService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AuthServiceConsumer
{



    @Autowired
    private UserService userService;


    @KafkaListener(topics = "${spring.kafka.topic-json.name}", groupId = "${spring.kafka.consumer.group-id}")
    public void listen(UserInfoDto eventData) {
        try{
            // Todo: Make it transactional, to handle idempotency and validate email, phoneNumber etc
            userService.createOrUpdateUser(eventData);
        }catch(Exception ex){
            System.out.println("AuthServiceConsumer: Exception is thrown while consuming kafka event");
        }
    }

}

// UserInfoDto --> UserinfoEntity
