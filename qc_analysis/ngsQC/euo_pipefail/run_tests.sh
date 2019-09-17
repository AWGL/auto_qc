#!/bin/bash


bash test_1.sh
if [ $? -eq 0 ];
then echo "test_1: system.exit=0";
elif [ $? -ne 0 ];
then echo "test_1: system.exit does not equal 0- send email";
fi


bash test_1b.sh
if [ $? -eq 0 ];
then echo "test_1b: system.exit=0";
elif [ $? -ne 0 ];
then echo "test_1b: system.exit does not equal 0 -send email";
fi


bash test_2.sh
if [ $? -eq 0 ];
then echo "test_2: system.exit=0";
elif [ $? -ne 0 ];
then echo "test_2: system.exit does not equal 0- send email";
fi


bash test_2b.sh
if [ $? -eq 0 ];
then echo "test_2b: system.exit=0";
elif [ $? -ne 0 ];
then echo "test_2b: system.exit does not equal 0- send email";
fi
