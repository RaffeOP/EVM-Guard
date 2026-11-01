pragma solidity 0.5.12;

contract Locker4945 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    address[] public members;

    function join() public {
        if (members.length < 16) members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < 16; i++) {
            if (i < members.length) members[i].balance;
        }
    }
}
