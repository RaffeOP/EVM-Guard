pragma solidity 0.8.20;

contract Locker4512 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }

    function ownerOf_() public view returns (address) { return owner; }
}
