

int main(int argc, char** argv){

testLabel:

    if (argc < 2){
        printf("HELLO, WORLD!\n");
        return 10 * 3 - 2;
    }

    goto testLabel;

    int a = 2;
    int b = 0;
    int c = a / b;
    return c;
}
