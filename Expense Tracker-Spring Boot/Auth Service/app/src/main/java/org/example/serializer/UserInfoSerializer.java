package org.example.serializer;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.kafka.common.serialization.Serializer;
import org.example.eventProducer.UserInfoEvent;
import org.example.model.UserInfoDto;

import java.util.Map;

public class UserInfoSerializer implements Serializer<UserInfoEvent> {

    @Override
    public void configure(Map<String, ?> configs, boolean isKey){
        // intentionally left blank
    }


        //hpw serializing is happening
    @Override
    public byte[] serialize(String arg0, UserInfoEvent arg1){
        byte[] retVal = null;
        ObjectMapper objectMapper = new ObjectMapper();
        try{
            retVal = objectMapper.writeValueAsString(arg1).getBytes();
        }catch (Exception ex){
            ex.printStackTrace();
        }
        return retVal;
    }

    @Override
    public void close(){
        // intentionally left blank
    }

}
