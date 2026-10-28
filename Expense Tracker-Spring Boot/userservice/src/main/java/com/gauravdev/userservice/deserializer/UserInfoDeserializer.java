package com.gauravdev.userservice.deserializer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gauravdev.userservice.entities.UserInfoDto;
import org.apache.kafka.common.serialization.Deserializer;

import java.util.Map;
import java.util.Objects;

public class UserInfoDeserializer implements Deserializer<UserInfoDto> {

    @Override
    public void configure(Map<String, ?> configs, boolean isKey) {
    }

    @Override
    public UserInfoDto deserialize(String arg0, byte[] arg1){
        ObjectMapper objectMapper = new ObjectMapper();
        UserInfoDto user = null;
        try{
            user = objectMapper.readValue(arg1, UserInfoDto.class);
        }catch (Exception ex){
            ex.printStackTrace();

        }

        return user;


    }
    @Override
    public void close(){}
}
